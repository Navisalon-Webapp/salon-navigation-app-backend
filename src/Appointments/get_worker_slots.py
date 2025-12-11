from flask import Blueprint, request, jsonify
from helper.utils import get_db_connection
from datetime import datetime, timedelta, time
import mysql.connector

get_worker_slots = Blueprint("get_worker_slots", __name__, url_prefix="/api")

@get_worker_slots.route("/employee/<int:eid>/available-slots", methods=["GET"])
def get_available_slots(eid):
    """
    Get available time slots for a worker on a specific date
    Query params:
    - date: YYYY-MM-DD (required)
    - duration: service duration in minutes (required)
    """
    date_str = request.args.get('date')
    duration_str = request.args.get('duration')
    
    if not date_str:
        return jsonify({"status": "failure", "message": "date parameter required"}), 400
    
    if not duration_str:
        return jsonify({"status": "failure", "message": "duration parameter required"}), 400
    
    try:
        if duration_str == 'null':
            duration_str = '30'
        service_duration = int(duration_str)
    except ValueError:
        return jsonify({"status": "failure", "message": "duration must be a number"}), 400
    
    try:
        request_date = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_week = request_date.strftime("%A").lower()  # Short day name like "Mon", "Tue"
    except ValueError:
        return jsonify({"status": "failure", "message": "invalid date format, use YYYY-MM-DD"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "failure", "message": "db connection error"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Get worker's schedule for the requested day of the week
        avail_query = """
            SELECT start_time, finish_time
            FROM schedule
            WHERE eid = %s AND day = %s
        """
        cursor.execute(avail_query, (eid, day_of_week))
        availability = cursor.fetchone()
        
        if not availability:
            cursor.close()
            conn.close()
            return jsonify([]), 200
        
        start_time = availability['start_time']
        finish_time = availability['finish_time']
        
        if isinstance(start_time, timedelta):
            start_time = (datetime.min + start_time).time()
        elif isinstance(start_time, datetime):
            start_time = start_time.time()
        elif isinstance(start_time, time):
            pass
        else:
            start_time = time(9, 0)
            
        if isinstance(finish_time, timedelta):
            finish_time = (datetime.min + finish_time).time()
        elif isinstance(finish_time, datetime):
            finish_time = finish_time.time()
        elif isinstance(finish_time, time):
            pass
        else:
            finish_time = time(17, 0)
        
        appt_query = """
            SELECT TIME(start_time) as start, TIME(expected_end_time) as end
            FROM appointments
            WHERE eid = %s AND DATE(start_time) = %s
            ORDER BY start_time
        """
        cursor.execute(appt_query, (eid, date_str))
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        slots = []
        current = datetime.combine(request_date, start_time)
        end = datetime.combine(request_date, finish_time)
        
        # Generate slots - allow the last slot if it starts before end time
        while current < end:
            slot_start_time = current.time()
            slot_end_dt = current + timedelta(minutes=service_duration)
            slot_end_time = slot_end_dt.time()
            
            # Skip this slot if the appointment would end after worker's finish time
            if slot_end_dt > end:
                break
            
            slot_str = slot_start_time.strftime("%H:%M")
            
            is_available = True
            for appt in appointments:
                appt_start = appt['start']
                appt_end = appt['end']
                
                if isinstance(appt_start, timedelta):
                    appt_start = (datetime.min + appt_start).time()
                if isinstance(appt_end, timedelta):
                    appt_end = (datetime.min + appt_end).time()
                
                if slot_start_time < appt_end and slot_end_time > appt_start:
                    is_available = False
                    break
            
            if is_available:
                slots.append(slot_str)
            
            current += timedelta(minutes=service_duration)
        
        return jsonify(slots), 200
        
    except mysql.connector.Error as err:
        if conn:
            conn.close()
        return jsonify({"status": "failure", "message": f"db error: {err}"}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"status": "failure", "message": f"error: {str(e)}"}), 500

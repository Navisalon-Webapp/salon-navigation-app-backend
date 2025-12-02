from flask import Blueprint, request, jsonify
from helper.utils import get_db_connection
from datetime import datetime, timedelta
import mysql.connector

get_avail_workers = Blueprint("get_avail_workers", __name__, url_prefix="/api")

@get_avail_workers.route("/business/<int:bid>/available-workers", methods=["GET"])
def get_available_workers(bid):
    """
    Get available workers for a business on a specific date/time
    Query params:
    - date: YYYY-MM-DD (optional, defaults to today)
    - start_time: HH:MM (optional)
    """
    date_str = request.args.get('date')
    start_time_str = request.args.get('start_time')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "failure", "message": "db connection error"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all approved workers for this business
        query = """
            SELECT e.eid, u.first_name, u.last_name,
                   GROUP_CONCAT(DISTINCT ex.expertise SEPARATOR ', ') as expertise
            FROM employee e
            JOIN users u ON e.uid = u.uid
            LEFT JOIN employee_expertise ee ON e.eid = ee.eid
            LEFT JOIN expertise ex ON ee.exp_id = ex.exp_id
            WHERE e.bid = %s AND e.approved = true
            GROUP BY e.eid, u.first_name, u.last_name
        """
        
        cursor.execute(query, (bid,))
        workers = cursor.fetchall()
        
        # If date and time are provided, filter by availability
        if date_str and start_time_str:
            try:
                request_date = datetime.strptime(date_str, "%Y-%m-%d")
                day_of_week = request_date.strftime("%A")
                
                filtered_workers = []
                for worker in workers:
                    # Check if worker has availability for this day
                    avail_query = """
                        SELECT start_time, finish_time
                        FROM schedule
                        WHERE eid = %s AND day = %s
                    """
                    cursor.execute(avail_query, (worker['eid'], day_of_week))
                    availability = cursor.fetchone()
                    
                    if availability:
                        # Convert start_time to comparable format
                        start_parts = start_time_str.split(':')
                        request_time = timedelta(hours=int(start_parts[0]), minutes=int(start_parts[1]))
                        
                        # Convert availability times to timedelta for comparison
                        avail_start = availability['start_time']
                        avail_finish = availability['finish_time']
                        
                        if isinstance(avail_start, datetime):
                            avail_start = timedelta(hours=avail_start.hour, minutes=avail_start.minute)
                        if isinstance(avail_finish, datetime):
                            avail_finish = timedelta(hours=avail_finish.hour, minutes=avail_finish.minute)
                        
                        # Check if requested time is within availability window
                        if avail_start <= request_time <= avail_finish:
                            # Check for conflicts with existing appointments
                            conflict_query = """
                                SELECT COUNT(*) as count
                                FROM appointments
                                WHERE eid = %s 
                                AND DATE(start_time) = %s
                                AND TIME(start_time) <= %s
                                AND TIME(expected_end_time) > %s
                            """
                            cursor.execute(conflict_query, (worker['eid'], date_str, start_time_str, start_time_str))
                            conflict = cursor.fetchone()
                            
                            if conflict['count'] == 0:
                                filtered_workers.append(worker)
                
                workers = filtered_workers
            except ValueError as e:
                pass  # If date parsing fails, return all workers
        
        result = [{
            "employee_id": w['eid'],
            "employee_first_name": w['first_name'],
            "employee_last_name": w['last_name'],
            "expertise": w['expertise'] or "No expertise listed"
        } for w in workers]
        
        cursor.close()
        conn.close()
        
        return jsonify(result), 200
        
    except mysql.connector.Error as err:
        if conn:
            conn.close()
        return jsonify({"status": "failure", "message": f"db error: {err}"}), 500

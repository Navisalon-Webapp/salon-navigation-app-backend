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
    sid = request.args.get('sid')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "failure", "message": "db connection error"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all approved workers for this business
        query = """
            SELECT
                e.eid AS employee_id,
                u.first_name AS employee_first_name,
                u.last_name AS employee_last_name,
                GROUP_CONCAT(DISTINCT s2.name SEPARATOR ', ') AS services
            FROM employee e
            JOIN users u ON e.uid = u.uid
            LEFT JOIN employee_services es2 ON e.eid = es2.eid
            LEFT JOIN services s2 ON es2.sid = s2.sid
            WHERE e.bid = %s AND e.approved = TRUE
            GROUP BY e.eid, u.first_name, u.last_name
        """
        
        cursor.execute(query, (bid,))
        workers = cursor.fetchall()

        if sid:
            cursor.execute("""
                SELECT eid
                FROM employee_services
                WHERE sid = %s
            """, (sid,))
            valid_eids = {row["eid"] for row in cursor.fetchall()}
            workers = [w for w in workers if w["employee_id"] in valid_eids]
        
        if not date_str or not start_time_str:
            cursor.close()
            conn.close()
            return jsonify(workers), 200

        # If date and time are provided, filter by availability
        if date_str and start_time_str:
            try:
                request_date = datetime.strptime(date_str, "%Y-%m-%d")
                day_of_week = request_date.strftime("%A").lower()
                request_time = datetime.strptime(start_time_str, "%H:%M").time()
                
                filtered_workers = []
                for worker in workers:
                    # Check if worker has availability for this day
                    avail_query = """
                        SELECT start_time, finish_time
                        FROM schedule
                        WHERE eid = %s AND LOWER(day) = %s
                    """
                    cursor.execute(avail_query, (worker['eid'], day_of_week))
                    availability = cursor.fetchone()
                    
                    if availability and (availability['start_time'] <= request_time < availability['finish_time']):

                            # Check for conflicts with existing appointments
                            conflict_query = """
                                SELECT COUNT(*) as count
                                FROM appointments
                                WHERE eid = %s 
                                AND DATE(start_time) = %s
                                AND TIME(start_time) < %s
                                AND TIME(expected_end_time) > %s
                                AND status = 'upcoming'
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
            "services": w['services'] or "No services listed"
        } for w in workers]
        
        cursor.close()
        conn.close()
        
        return jsonify(result), 200
        
    except mysql.connector.Error as err:
        if conn:
            conn.close()
        return jsonify({"status": "failure", "message": f"db error: {err}"}), 500

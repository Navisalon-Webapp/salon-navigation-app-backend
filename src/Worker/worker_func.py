import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from .queries import query_eid, query_appointments, query_availability

load_dotenv()

def get_db_connection():
    """create database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            port=int(os.getenv("DB_PORT")),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_eid(uid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute(query_eid,[uid])
    result = cursor.fetchone()
    return result

def get_appointments(eid, date_filter=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    if date_filter:
        query = """
        SELECT a.aid, a.start_time, a.expected_end_time, u.first_name, u.last_name, s.name as service_name, s.duration
        FROM appointments a
        LEFT JOIN customers c ON a.cid = c.cid
        LEFT JOIN users u ON c.uid = u.uid
        LEFT JOIN services s ON a.sid = s.sid
        WHERE a.eid = %s 
        AND DATE(a.start_time) = %s
        ORDER BY a.start_time
        """
        cursor.execute(query, [eid, date_filter])
    else:
        query = """
        SELECT a.aid, a.start_time, a.expected_end_time, a.notes, u.first_name, u.last_name, s.name as service_name, s.duration
        FROM appointments a
        LEFT JOIN customers c ON a.cid = c.cid
        LEFT JOIN users u ON c.uid = u.uid
        LEFT JOIN services s ON a.sid = s.sid
        WHERE a.eid = %s 
        AND a.start_time > CURRENT_TIMESTAMP()
        ORDER BY a.start_time
        """
        cursor.execute(query, [eid])
    
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_avail(eid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute(query_availability,[eid])
    schedule = cursor.fetchall()
    print(schedule)
    return schedule

def insert_avail(eid, week_data):
    from datetime import datetime
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    try:
        # First, delete all existing schedules for this employee
        cursor.execute("DELETE FROM schedule WHERE eid = %s", [eid])
        
        for day, info in week_data.items():
            if info["enabled"]:
                # Parse time strings (HH:MM)
                start_parts = info["start"].split(":")
                end_parts = info["end"].split(":")
                
                # Create time-only timestamps using a reference date (1970-01-01)
                start_time = datetime(1970, 1, 1, int(start_parts[0]), int(start_parts[1]), 0)
                finish_time = datetime(1970, 1, 1, int(end_parts[0]), int(end_parts[1]), 0)
                
                
                
                # Insert the schedule entry with the day column
                cursor.execute(
                    "INSERT INTO schedule (eid, day, start_time, finish_time) VALUES (%s, %s, %s, %s)",
                    [eid, day.lower(), start_time, finish_time]
                )
        
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Database error in insert_avail: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
    return True
    
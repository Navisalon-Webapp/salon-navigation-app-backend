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
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_eid(uid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query_eid,[uid])
    result = cursor.fetchone()
    return result

def get_appointments(eid, date_filter=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if date_filter:
        query = """
        SELECT a.aid, a.start_time, a.expected_end_time, a.notes, u.first_name, u.last_name, s.name as service_name, s.durationMin
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
        SELECT a.aid, a.start_time, a.expected_end_time, a.notes, u.first_name, u.last_name, s.name as service_name, s.durationMin
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query_availability,[eid])
    schedule = cursor.fetchall()
    return schedule

def insert_avail(eid, week_data):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    for day, info in week_data.items():
        if info["enabled"]:
            # Check if that day is already in worker's schedule
            cursor.execute("SELECT sched_id FROM schedule WHERE eid = %s AND day = %s",[eid, day])
            exists = cursor.fetchone()

            if exists:
                cursor.execute("UPDATE schedule SET start_time = %s, finish_time = %s WHERE sched_id = %s",
                               [info["start"], info["end"], exists["sched_id"]])
            else:
                cursor.execute("INSERT INTO schedule (eid, day, start_time, finish_time) VALUES (%s, %s, %s, %s)",
                        [eid, day, info["start"], info["end"]]
                    )    
        else:
            # If day exists but is not selected
            cursor.execute("DELETE FROM schedule WHERE eid = %s AND day = %s",
                    [eid, day],
                )
    
    conn.commit()
    cursor.close()
    conn.close()
    return True    
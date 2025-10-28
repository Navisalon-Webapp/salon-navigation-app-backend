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

def get_appointments(eid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query_appointments,[eid])
    result = cursor.fetchall()
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
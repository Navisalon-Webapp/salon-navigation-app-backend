import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from .queries import query_eid, query_appointments

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

    
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from flask_login import current_user
from .queries import query_upcoming_appointments

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
    
def get_curr_cid():
    """Return the customer ID for the currently logged-in user, or raise an error if none exists."""
    uid = getattr(current_user, "id", None)
    if uid is None:
        raise ValueError("Current user is not logged in")

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT cid FROM customers WHERE uid = %s", [uid])
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result or result["cid"] is None:
            raise ValueError("Customer ID not found for current user")
        return result["cid"]
    except Exception as e:
        conn.close()
        raise e
    
def get_upcoming_appointments():
    """return all upcoming appointments for all customers"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_upcoming_appointments)
        results = cursor.fetchall()
        return results
    except Exception as e:
        conn.close()
        raise e
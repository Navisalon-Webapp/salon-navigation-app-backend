import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from flask_login import current_user
from .queries import *

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
    
def get_curr_bid():
    """Return the business ID for the currently logged-in user, or raise an error if none exists."""
    uid = getattr(current_user, "id", None)
    if uid is None:
        raise ValueError("Current user is not logged in")

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT bid FROM business WHERE uid = %s", [uid])
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result or result["bid"] is None:
            raise ValueError("Businsess ID not found for current user")
        return result["bid"]
    except Exception as e:
        conn.close()
        raise e
    
def get_curr_eid():
    """Return the employee ID for the currently logged-in user, or raise an error if none exists."""
    uid = getattr(current_user, "id", None)
    if uid is None:
        raise ValueError("Current user is not logged in")

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT eid FROM employee WHERE uid = %s", [uid])
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result or result["eid"] is None:
            raise ValueError("Employee ID not found for current user")
        return result["eid"]
    except Exception as e:
        conn.close()
        raise e

def check_role(uid):
    """return role of user"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_user_role,[uid])
        role=cursor.fetchone()
        return role['name']
    except Exception as e:
        conn.close()
        raise e
    
def get_email(uid):
    """return email of user"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_email,[uid])
        email = cursor.fetchone()
        return email['email']
    except Exception as e:
        conn.close()
        raise e
    
def get_name(uid):
    """return ['first name', 'last name'] of user"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    cursor = None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query_name,[uid])
        name = cursor.fetchone()
        return name 
    except Exception as e:
        conn.close()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
def get_appointment_details(aid):
    """return cid, customer first name, customer last name, customer email,
    
    eid, employee first name, employee last name, 
    
    bid, business name, business address fields,
    
    sid, service name, service duration,
    
    aid, appointment start time, appointment expected end time"""

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_appointment, [aid])
        results = cursor.fetchone()
        return results
    except Exception as e:
        conn.close()
        raise e
    finally:
        if not conn.is_connected():
            conn.close
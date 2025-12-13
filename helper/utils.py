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
            port=int(os.getenv("DB_PORT")),
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
        cursor = conn.cursor(dictionary=True, buffered=True)
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
        cursor = conn.cursor(dictionary=True, buffered=True)
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
        cursor = conn.cursor(dictionary=True, buffered=True)
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
    
def get_bid_from_uid(uid):
    if uid is None:
        raise ValueError("Current user is not logged in")

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
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

def checkrole(uid):
    """return role of user"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute(query_user_role,[uid])
        role=cursor.fetchone()
        cursor.close()
        conn.close()
        return role['name']
    except Exception as e:
        if conn:
            conn.close()
        raise e

def check_role():
    """return role of user"""
    uid = getattr(current_user, "id", None)
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute(query_user_role,[uid])
        role=cursor.fetchone()
        cursor.close()
        conn.close()
        return role['name']
    except Exception as e:
        if conn:
            conn.close()
        raise e
    
def get_email(uid):
    """return email of user"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute(query_email,[uid])
        email = cursor.fetchone()
        cursor.close()
        conn.close()
        return email['email']
    except Exception as e:
        if conn:
            conn.close()
        raise e
    
def get_name(uid):
    """return ['first name', 'last name'] of user"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    cursor = None
    
    try:
        cursor = conn.cursor(buffered=True)
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

def get_uid_for_eid(conn, eid):
    """return uid for given eid"""
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT uid FROM employee WHERE eid = %s", [eid])
        result = cursor.fetchone()
        cursor.close()
        return result['uid'] if result else None
    except Exception as e:
        if cursor:
            cursor.close()
        raise e
    
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
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute(query_appointment, [aid])
        results = cursor.fetchone()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        if conn:
            conn.close()
        raise e
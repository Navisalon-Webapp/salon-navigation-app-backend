import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from flask_login import current_user
from flask import current_app
from flask_mail import Message
from src.extensions import mail
from .queries import *
from datetime import datetime

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
    
def create_message(aid) -> Message:

    details = get_appointment_details(aid)
    eid = details['eid']
    minute = details['start_time'].minute
    if minute < 10:
        minute = f"0{minute}"
    else:
        minute = f"{minute}"

    if eid:
        message = f"""You have an appointment tomorrow at {details['salon']} with {details['employee_first']} {details['employee_last']} at {details['start_time'].hour}:{details['start_time'].minute}
        Address
        {details['street']}
        {details['city']}, {details['state']}
        {details['country']}
        {details['zip_code']}
        """
    else:
        message = f"""You have an appointment tomorrow at {details['salon']} at {details['start_time'].hour}:{minute}\n
        Address\n
        {details['street']}\n
        {details['city']}, {details['state']}\n
        {details['country']}\n
        {details['zip_code']}"""
    msg = Message(f"Hello {details['customer_first']} {details['customer_last']}")
    msg.body = message
    return msg

def email_appointment(app ,msg: Message, to):
    with app.app_context():
        msg.sender = os.getenv('MAIL_USERNAME')
        msg.recipients = [to]
        mail.send(msg)
        print(f"Sent email to {to} at {datetime.now()}")

def check_appointment_subscription(cid) -> bool:
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_email_subscriptions, [cid])
        results = cursor.fetchone()
        cursor.close()
        conn.close()
        return results['appointment']
    except Exception as e:
        conn.close()
        raise e
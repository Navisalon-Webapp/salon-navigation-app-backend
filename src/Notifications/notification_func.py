import os
from dotenv import load_dotenv
from flask_mail import Message
from src.extensions import mail
from .queries import *
from datetime import datetime
from helper.utils import *

load_dotenv()
        
def create_appt_message(aid) -> Message:

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

def create_promo_message(title, description, business):
    msg = Message(subject=title, body=description)
    msg.subject = msg.subject + f"at {business}"
    return msg

def email_message(app, msg:Message, to):
    with app.app_context():
        msg.sender = os.getenv('MAIL_USERNAME')
        msg.recipients = to
        mail.send(msg)
        print(f"Sent email to {to} at {datetime.now()}")

def check_appointment_subscription(cid) -> bool:
    """Return true if user wants to recieve appointment emails
    
    otherwise return
    """
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
    
def check_promotion_subscription(cid) -> bool:
    """Return true if user wants to recieve promotion emails
    
    otherwise return
    """
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_email_subscriptions, [cid])
        results = cursor.fetchone()
        cursor.close()
        conn.close()
        return results['promotion']
    except Exception as e:
        conn.close()
        raise e
    
def get_business_customers(bid):
    """Return all customers that have made appointments at a business"""
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_customers_business, [bid])
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        return customers
    except Exception as e:
        conn.close()
        raise e

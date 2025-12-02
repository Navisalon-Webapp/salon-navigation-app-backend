import os
from dotenv import load_dotenv
from flask_mail import Message
from src.extensions import mail
from .queries import *
from datetime import datetime
from helper.utils import *
import requests

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
    
def send_password_reset(email, uid):
    # Check if Mailgun is configured (works in both dev and production)
    mailgun_api_key = os.getenv('MAILGUN_API_KEY')
    mailgun_domain = os.getenv('MAILGUN_DOMAIN')
    
    if mailgun_api_key and mailgun_domain:
        # Use Mailgun API
        reset_link = f"{os.getenv('FRONTEND')}/password-reset/{uid}"
        
        # Always print the link for development/testing
        print(f"\n{'='*60}")
        print(f"PASSWORD RESET for {email}")
        print(f"Reset link: {reset_link}")
        print(f"{'='*60}\n")
        
        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=("api", mailgun_api_key),
                data={
                    "from": f"Navisalon <mailgun@{mailgun_domain}>",
                    "to": [email],
                    "subject": "Password Reset",
                    "html": f"""
                    <p>Follow this link to reset your account password</p>
                    <p><a href="{reset_link}" style="color: blue; text-decoration: underline;">
                    Password Reset
                    </a></p>
                    """
                }
            )
            
            if response.status_code == 200:
                print(f"Password reset email sent to {email} via Mailgun")
                return True
            else:
                print(f"Mailgun error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Failed to send via Mailgun: {e}")
            return False
    
    # Fallback: use Gmail SMTP if configured
    mail_username = os.getenv('MAIL_USERNAME')
    
    if not mail_username:
        # No email configured, just log the reset link
        reset_link = f"{os.getenv('FRONTEND')}/password-reset/{uid}"
        print(f"\n{'='*60}")
        print(f"PASSWORD RESET REQUESTED for {email}")
        print(f"Reset link: {reset_link}")
        print(f"{'='*60}\n")
        return True
    
    msg = Message(
        subject = 'Password Reset',
        sender = mail_username,
        recipients=[email]
    )
    msg.html = f"""
    <p>Follow this link to reset your account password</p>
    <p><a href="{os.getenv('FRONTEND')}/password-reset/{uid}" style="color: blue; text-decoration: underline;">
    Password Reset
    </a></p>
    """
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False


from flask import Blueprint, request, jsonify
from flask_mail import Message
from src.Notifications.notification_func import *
from src.extensions import scheduler
from src.extensions import mail
from datetime import date, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

notification = Blueprint("notification",__name__,url_prefix='/notification')

@notification.route('/upcoming-appointments',methods=['GET'])
def get_appointments():
    return jsonify(get_upcoming_appointments())

@notification.route('/appointment',methods=['POST'])
def email_appointment():
    msg = Message('Hello', sender =os.getenv('MAIL_USERNAME'), recipients = [os.getenv('MAIL_RECIEVER')] )
    msg.body = 'Hello Flask message sent from Flask-Mail'
    mail.send(msg)
    return jsonify('sent')

@scheduler.task('interval', id='test', seconds=120, misfire_grace_time=900)
def test_scheduler():
    appointments = get_upcoming_appointments()
    for a in appointments:
        tomorrow = date.today() + timedelta(days=1)
        if a['start_time'].date() != tomorrow:
            continue
        if a['eid']:
            message = f"You have an appointment today at {a['salon']} with {a['employee_first']} {a['employee_last']} at {a['start_time'].hour}:{a['start_time'].minute}"
        else:
            message = f"You have an appointment today at {a['salon']} at {a['start_time'].hour}:{a['start_time'].minute}"
        print(f"Hello {a['customer_first']} {a['customer_last']}\n",message)

@scheduler.task('interval', id='email_reminder', seconds=120, misfire_grace_time=900)
def email_reminders():
    appointments = get_upcoming_appointments()
    for a in appointments:
        tomorrow = date.today() + timedelta(days=1)
        if a['start_time'].date() != tomorrow:
            continue
        if a['eid']:
            message = f"You have an appointment today at {a['salon']} with {a['employee_first']} {a['employee_last']} at {a['start_time'].hour}:{a['start_time'].minute}"
        else:
            message = f"You have an appointment today at {a['salon']} at {a['start_time'].hour}:{a['start_time'].minute}"
        msg = Message(f"Hello {a['customer_first']} {a['customer_last']}", sender=os.getenv('MAIL_USERNAME'), recipients = [os.getenv('MAIL_RECIEVER')] )
        # msg = Message(f"Hello {a['customer_first']} {a['customer_last']}", sender=os.getenv('MAIL_USERNAME'), recipients = [a['email']] )
        msg.body = message
        mail.send(msg)
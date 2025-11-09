from flask import Blueprint, request, jsonify
from src.Notifications.notification_func import *
from helper.utils import *
from src.extensions import mail
from flask_mail import Message
from dotenv import load_dotenv
from src.extensions import scheduler
from flask_login import current_user, login_required
import os

load_dotenv()

notification = Blueprint("notification",__name__,url_prefix='/notification')

@notification.route('/employee-late', methods=['PUT'])
@login_required
def notify_late():
    uid =  current_user.id
    if not check_role(uid) == "employee":
        return jsonify({
            "status":"failure",
            "message":"current user not an employee"
        }), 403
    eid = get_curr_eid()
    
    data = request.get_json()
    aid = data['aid']
    new_time_raw = data['new_time']

    appt_details = get_appointment_details(aid)
    if not appt_details['eid'] == eid:
        return jsonify({
            "status":"failure",
            "message":"employee assigned to employee does not match current user"
        }), 403

    try:
        if "T" in new_time_raw and new_time_raw.count(":") >= 1:
            start_time = datetime.fromisoformat(new_time_raw)
        else:
            start_time = datetime.strptime(new_time_raw, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return jsonify({"status": "failure", "message": f"invalid start_time: {e}"}), 400
    
    if start_time <= appt_details['start_time'] or start_time <= datetime.now():
        return jsonify({"status": "failure", "message": f"invalid start_time: {e}"}), 400
    
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute()
    except Exception as e:
        conn.close()
        raise e
    
    



    

    

    

@notification.route('/upcoming-appointments',methods=['GET'])
def get_appointments():
    return jsonify(get_upcoming_appointments())

@notification.route('/appointment',methods=['GET'])
def get_appointment():
    data = request.get_json()
    aid = data['aid']
    return jsonify(get_appointment_details(aid))

@notification.route('/get-jobs', methods=['GET'])
def get_jobs():
    print(scheduler.get_jobs())
    return jsonify("hello")

@notification.route('/test_email',methods=['POST'])
def email_appointment():
    msg = Message('Hello', sender =os.getenv('MAIL_USERNAME'), recipients = [os.getenv('MAIL_USERNAME')] )
    msg.body = 'Hello Flask message sent from Flask-Mail'
    mail.send(msg)
    return jsonify('sent')
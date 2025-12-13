# src/Appointments/create_appointment.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_mail import Mail, Message
from src.extensions import scheduler, mail
from src.Notifications.notification_func import *
from helper.utils import *
from datetime import datetime, timedelta
from .app_func import  *
import pytz

schedule_appt = Blueprint("schedule_appt", __name__, url_prefix="/api")

def send_reminder(msg : Message, email):
    from app import app
    from flask import current_app
    try:
        app_context = current_app._get_current_object()
    except RuntimeError:
        app_context = app
    with app_context.app_context():
        email_message(current_app._get_current_object(),msg,[email])

# GET services from business
@schedule_appt.route("/business/<int:bid>/services", methods=["GET"])
def business_services(bid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "Failure",
                        "message": "Error connecting to db"}), 500
    cur = conn.cursor(dictionary=True, buffered=True)
    cur.execute("SELECT sid, name, price, duration FROM services WHERE bid = %s", (bid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200

# POST schedule appointment
@schedule_appt.route("/client/create-appointment", methods=["POST"])
def create_appointment():
    """
    POST JSON body expects:
    {
      "sid": <service id> (required),
      "start_time": "<YYYY-MM-DDTHH:MM>" or "<ISO string>" (required),
      "expected_end_time": "YYYY-MM-DD HH:MM:SS" (recommended but server will compute if missing),
      "eid": <employee id> (optional),
      "notes": "optional text"
      // optionally for non-logged-in or test: "cid": <customer id>
    }
    """
    data = request.get_json() or {}
    sid = data.get("sid")
    start_time_raw = data.get("start_time")
    expected_end_time_raw = data.get("expected_end_time")
    eid = data.get("eid")  # optional
    notes = data.get("notes", "")

    if not sid or not start_time_raw:
        return jsonify({"status": "failure", "message": "sid and start_time required"}), 400

    try:
        if "T" in start_time_raw and start_time_raw.count(":") >= 1:
            start_dt = datetime.fromisoformat(start_time_raw)
        else:
            start_dt = datetime.strptime(start_time_raw, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return jsonify({"status": "failure", "message": f"invalid start_time: {e}"}), 400

    # Check if the appointment time is in the past
    # Use Eastern Time for comparison to handle timezone differences
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.now(eastern)
    
    # Make start_dt timezone-aware (assume it's in Eastern time from frontend)
    if start_dt.tzinfo is None:
        start_dt_eastern = eastern.localize(start_dt)
    else:
        start_dt_eastern = start_dt.astimezone(eastern)
    
    # Allow appointments up to 5 minutes in the past to account for slight clock differences
    if start_dt_eastern < now_eastern - timedelta(minutes=5):
        return jsonify({"status": "failure", "message": "Cannot book appointments in the past"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "failure", "message": "db connection error"}), 500

    try:
        cid = None
        if hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
            cid = get_cid_for_uid(conn, current_user.id)
            if cid is None:
                return jsonify({"status": "failure", "message": "current user not a customer (no cid)"}), 403
        else:
            cid = data.get("cid")
            if not cid:
                return jsonify({"status": "failure", "message": "not authenticated and no cid provided"}), 403

        if expected_end_time_raw:
            expected_dt = datetime.fromisoformat(expected_end_time_raw) if "T" in expected_end_time_raw else datetime.strptime(expected_end_time_raw, "%Y-%m-%d %H:%M:%S")
        else:
            expected_dt = start_dt + timedelta(minutes=60)

        # convert datetimes for db
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        expected_str = expected_dt.strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.cursor(buffered=True)
        
        # Get service price and business ID
        service_query = "SELECT price, bid FROM services WHERE sid = %s"
        cur.execute(service_query, (sid,))
        service_result = cur.fetchone()
        
        if not service_result:
            cur.close()
            conn.close()
            return jsonify({"status": "failure", "message": "Service not found"}), 404
        
        service_price = float(service_result[0])
        business_id = service_result[1]
        
        # Insert appointment
        insert_q = """
            INSERT INTO appointments (cid, eid, sid, start_time, expected_end_time)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(insert_q, (cid, eid, sid, start_str, expected_str))
        conn.commit()
        new_aid = cur.lastrowid

        if notes.strip():
            author_uid = current_user.id if hasattr(current_user, "id") else None
            author_role = check_role() if hasattr(current_user, "id") else "client"
            note_q = """
                INSERT INTO appointment_notes (aid, author_uid, author_role, note_text)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(note_q, (new_aid, author_uid, author_role, notes))
            conn.commit()
        
        # Create transaction record for the appointment
        transaction_query = """
            INSERT INTO transactions (cid, bid, aid, amount)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(transaction_query, (cid, business_id, new_aid, service_price))
        conn.commit()
        
        cur.close()
        conn.close()

        if check_appointment_subscription(cid):
            msg = create_appt_message(new_aid)
            email = current_user.email
            run_time = start_dt - timedelta(days=1)
            
            # Use Eastern timezone for scheduling
            eastern = pytz.timezone('US/Eastern')
            now_eastern = datetime.now(eastern)
            
            # Make run_time timezone-aware
            if run_time.tzinfo is None:
                run_time = eastern.localize(run_time)
            
            if now_eastern >= run_time:
                run_time = now_eastern + timedelta(seconds=10)
                
            scheduler.add_job(
                func=lambda:send_reminder(msg, email),
                trigger='date',
                run_date=run_time,
                id=f'Appointment:{new_aid}:{cid}'
            )

        return jsonify({"status": "success", "message": "appointment created", "appointment_id": new_aid}), 201

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"status": "failure", "message": f"db error: {err}"}), 500
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"status": "failure", "message": f"error: {e}"}), 500
    
@schedule_appt.route('/employee/reschedule', methods=['PUT'])
@login_required
def employee_reschedule():
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

    if not aid or not new_time_raw:
        return jsonify({
            "status":"failure",
            "message":"aid and new_time_raw required"
        }), 400

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
    
    # Use Eastern timezone for validation
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.now(eastern)
    
    # Make start_time timezone-aware
    if start_time.tzinfo is None:
        start_time = eastern.localize(start_time)
    
    if start_time <= appt_details['start_time'] or start_time <= now_eastern:
        return jsonify({"status": "failure", "message": "invalid start_time: must be in the future"}), 400
    
    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")
    cursor = None
    cid = appt_details['cid']
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("select duration from services where sid = %s", [appt_details['sid']])
        row=cursor.fetchone()
        duration=row['duration']

        end_time = start_time + timedelta(minutes=duration)

        start_str=start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_str=end_time.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("update appointments set start_time=%s, expected_end_time=%s where aid=%s",[start_str, end_str, aid])
        conn.commit()

        # Remove old scheduled reminder job if exists
        if scheduler.get_job(f"Appointment:{aid}:{cid}"):
            scheduler.remove_job(f"Appointment:{aid}:{cid}")
        
        # Schedule new reminder email (24 hours before)
        reminder_time = start_time - timedelta(hours=24)
        if reminder_time > now_eastern:
            c_email = get_email(appt_details['c_uid'])
            msg = Message(subject="Appointment Reminder", body=f"You have an appointment tomorrow at {start_time.strftime('%I:%M %p')}")
            
            scheduler.add_job(
                func=lambda: send_reminder(msg, c_email),
                trigger='date',
                run_date=reminder_time,
                id=f'Appointment:{aid}:{cid}'
            )

        c_name = get_name(appt_details['c_uid'])
        c_email = get_email(appt_details['c_uid'])
        e_name = get_name(current_user.id)
        e_email = get_email(current_user.id)

        if check_appointment_subscription(appt_details['cid']):
            message = f"Your appointment with {e_name[0]} {e_name[1]} has been rescheduled to {'{:d}:{:02d}'.format(start_time.hour, start_time.minute)}"
            msg = Message(subject=f"Hello {c_name[0]} {c_name[1]}", body=message)
            send_reminder(msg, c_email)
        
        message = f"Your appointment with {c_name[0]} {c_name[1]} has been rescheduled to {'{:d}:{:02d}'.format(start_time.hour, start_time.minute)}"
        msg = Message(subject="Appointment Rescheduled", body=message)
        send_reminder(msg, e_email)

        return jsonify({
            "status":"success",
            "message":"Appointment has been rescheduled"
        }), 200
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"status": "failure", "message": f"db error: {e}"}), 500
    except Exception as e:
        conn.close()
        raise e
    finally:
        if cursor:
            conn.close()
        if conn:
            conn.close()

@schedule_appt.route('/employee/send-notification/<int:aid>', methods=['POST'])
@login_required
def send_appointment_notification(aid):
    uid = current_user.id
    if not check_role(uid) == "employee":
        return jsonify({
            "status": "failure",
            "message": "current user not an employee"
        }), 403
    
    eid = get_curr_eid()
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "failure", "message": "db connection error"}), 500
    
    cursor = None
    try:
        appt_details = get_appointment_details(aid)
        
        if not appt_details:
            return jsonify({
                "status": "failure",
                "message": "appointment not found"
            }), 404
        
        if appt_details['eid'] != eid:
            return jsonify({
                "status": "failure",
                "message": "appointment not assigned to current employee"
            }), 403
        
        c_name = get_name(appt_details['c_uid'])
        c_email = get_email(appt_details['c_uid'])
        e_name = get_name(current_user.id)
        
        start_time = appt_details['start_time']
        time_str = '{:d}:{:02d}'.format(start_time.hour, start_time.minute)
        date_str = start_time.strftime("%B %d, %Y")
        
        message = f"Hello {c_name[0]} {c_name[1]},\n\nThis is a notification from {e_name[0]} {e_name[1]} regarding your appointment on {date_str} at {time_str}.\n\nI may be running a few minutes late. Thank you for your patience!\n\nBest regards,\n{e_name[0]} {e_name[1]}"
        msg = Message(
            subject=f"Update: Appointment on {date_str}",
            body=message,
            recipients=[c_email]
        )
        
        mail.send(msg)
        
        return jsonify({
            "status": "success",
            "message": "notification sent successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": f"error sending notification: {str(e)}"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

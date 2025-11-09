# src/Appointments/create_appointment.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_mail import Mail, Message
from src.extensions import scheduler
from src.Notifications.notification_func import email_appointment, create_appt_message, check_appointment_subscription
from datetime import datetime, timedelta
from .app_func import  *

schedule_appt = Blueprint("schedule_appt", __name__, url_prefix="/api")

def send_reminder(msg, email):
    from app import app
    from flask import current_app
    try:
        app_context = current_app._get_current_object()
    except RuntimeError:
        app_context = app
    with app_context.app_context():
        email_appointment(current_app._get_current_object(),msg,email)

# GET services from business
@schedule_appt.route("/business/<int:bid>/services", methods=["GET"])
def business_services(bid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "Failure",
                        "message": "Error connecting to db"}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT sid, name, price FROM services WHERE bid = %s", (bid,))
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

        cur = conn.cursor()
        insert_q = """
            INSERT INTO appointments (cid, eid, sid, start_time, expected_end_time, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(insert_q, (cid, eid, sid, start_str, expected_str, notes))
        conn.commit()
        new_aid = cur.lastrowid
        cur.close()
        conn.close()

        if check_appointment_subscription(cid):
            msg = create_appt_message(new_aid)
            email = current_user.email
            run_time = start_dt - timedelta(days=1) 
            if datetime.now() >= run_time:
                run_time = datetime.now() + timedelta(seconds=10)
            scheduler.add_job(
                func=lambda:send_reminder(msg, email),
                trigger='date',
                run_date=run_time,
                id=f'Appointment:{new_aid}:{cid}'
            )

        return jsonify({"status": "success", "message": "appointment created", "appointment_id": new_aid}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"status": "failure", "message": f"db error: {err}"}), 500
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"status": "failure", "message": f"error: {e}"}), 500

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *
from .queries import *
from datetime import datetime

business_appointments = Blueprint("business_appointments", __name__, url_prefix="/business/appointments")

@business_appointments.route('/future', methods=['GET'])
@login_required
def get_future_business_appointments():
    bid = get_curr_bid()
    if check_role() != 'business' or not bid:
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_future_appointments, [bid])
        appointments = cursor.fetchall()
        appointments_formatted = []
        for a in appointments:
            appt = {
                'id': a['aid'],
                'client': f"{a['customer_first']} {a['customer_last']}",
                'time': a['start_time'].time().isoformat(),
                'date': a['start_time'].date().isoformat(),
                'service': a['service'],
                'durationMins': a['durationMin'],
                'notes': a['note'],
                'status': 'incomplete'
            }
            appointments_formatted.append(appt)
        return jsonify(appointments_formatted), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@business_appointments.route('/past', methods=['GET'])
@login_required
def get_past_business_appointments():
    bid = get_curr_bid()
    if check_role() != 'business' or not bid:
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_past_appointments, [bid])
        appointments = cursor.fetchall()
        appointments_formatted = []
        for a in appointments:
            appt = {
                'id': a['aid'],
                'client': f"{a['customer_first']} {a['customer_last']}",
                'time': a['start_time'].time().isoformat(),
                'date': a['start_time'].date().isoformat(),
                'service': a['service'],
                'durationMins': a['durationMin'],
                'notes': a['note'],
                'status': 'incomplete'
            }
            if a['end_time'] is not None:
                duration = a['start_time'] - a['end_time']
                appt['durationMins'] = duration.total_seconds() // 60
                appt['status'] = 'complete'
            else: appt['status'] = 'incomplete'
            appointments_formatted.append(appt)
        return jsonify(appointments_formatted), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@business_appointments.route('/cancel/<int:aid>', methods=['DELETE'])
@login_required
def cancel_appointment(aid):
    bid = get_curr_bid()
    if check_role() != 'business' or not bid:
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    appointment = get_appointment_details(aid)
    if appointment is None:
        print("could not find appointment")
        print("appointment should not be in the past")
        return jsonify({
            "status":"failure",
            "message":"could not find appointment"
        }), 400
    if appointment['bid'] != bid:
        print("User does not have permission to cancel this appointment")
        return jsonify({
            "status":"failure",
            "message":"User does not have permission to cancel this appointment"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(delete_appointment, [aid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"deleted appointment",
            "appointment id": aid
        })
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
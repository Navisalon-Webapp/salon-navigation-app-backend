from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .worker_func import *
from datetime import datetime

appointments = Blueprint("appointments",__name__,url_prefix='/worker')

@appointments.route('/appointments')
@login_required
def list_appointments():
    if(current_user.role != "employee"):
        return jsonify({
            "status": "failure",
            "message": "user is not an employee",
            "user_role": current_user.role
        }), 403
    
    date_param = request.args.get('date')
    
    eid = get_eid(current_user.id)
    if not eid:
        return jsonify({
            "status": "failure",
            "message": "employee not found"
        }), 404
    
    appointments = get_appointments(eid['eid'], date_param)
    
    formatted_appointments = []
    for appt in appointments:
        start_time = appt.get('start_time')
        if isinstance(start_time, datetime):
            time_str = start_time.strftime('%I:%M %p')
        else:
            time_str = str(start_time)
        
        formatted_appointments.append({
            "id": str(appt.get('aid')),
            "time": time_str,
            "client": f"{appt.get('first_name', '')} {appt.get('last_name', '')}".strip() or "Unknown Client",
            "service": appt.get('service_name', 'N/A'),
            "duration": appt.get('duration', 60),
            "status": "scheduled"
        })

        # loop through rows to append notes
    
    return jsonify(formatted_appointments), 200

@appointments.route('/past-appointments')
@login_required
def list_past_appointments():
    if(current_user.role != "employee"):
        return jsonify({
            "status": "failure",
            "message": "user is not an employee",
            "user_role": current_user.role
        }), 403
    
    eid = get_eid(current_user.id)
    if not eid:
        return jsonify({
            "status": "failure",
            "message": "employee not found"
        }), 404
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    query = """
    SELECT a.aid, a.start_time, a.expected_end_time, u.first_name, u.last_name, s.name as service_name, s.duration
    FROM appointments a
    LEFT JOIN customers c ON a.cid = c.cid
    LEFT JOIN users u ON c.uid = u.uid
    LEFT JOIN services s ON a.sid = s.sid
    WHERE a.eid = %s 
    AND a.start_time < CURRENT_TIMESTAMP()
    ORDER BY a.start_time DESC
    """
    cursor.execute(query, [eid['eid']])
    
    past_appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    
    formatted_appointments = []
    for appt in past_appointments:
        start_time = appt.get('start_time')
        if isinstance(start_time, datetime):
            time_str = start_time.strftime('%I:%M %p')
            date_str = start_time.strftime('%m/%d/%Y')
        else:
            time_str = str(start_time)
            date_str = ""
        
        formatted_appointments.append({
            "id": str(appt.get('aid')),
            "time": time_str,
            "date": date_str,
            "client": f"{appt.get('first_name', '')} {appt.get('last_name', '')}".strip() or "Unknown Client",
            "service": appt.get('service_name', 'N/A'),
            "duration": appt.get('duration', 60),
            "status": "completed"
        })
    
    return jsonify(formatted_appointments), 200


@appointments.route('/future-appointments')
@login_required
def list_future_appointments():
    if(current_user.role != "employee"):
        return jsonify({
            "status": "failure",
            "message": "user is not an employee",
            "user_role": current_user.role
        }), 403
    
    eid = get_eid(current_user.id)
    if not eid:
        return jsonify({
            "status": "failure",
            "message": "employee not found"
        }), 404
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    query = """
    SELECT a.aid, a.start_time, a.expected_end_time, u.first_name, u.last_name, s.name as service_name, s.duration
    FROM appointments a
    LEFT JOIN customers c ON a.cid = c.cid
    LEFT JOIN users u ON c.uid = u.uid
    LEFT JOIN services s ON a.sid = s.sid
    WHERE a.eid = %s 
    AND a.start_time >= CURRENT_TIMESTAMP()
    ORDER BY a.start_time ASC
    """
    cursor.execute(query, [eid['eid']])
    
    future_appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    
    formatted_appointments = []
    for appt in future_appointments:
        start_time = appt.get('start_time')
        if isinstance(start_time, datetime):
            time_str = start_time.strftime('%I:%M %p')
            date_str = start_time.strftime('%m/%d/%Y')
        else:
            time_str = str(start_time)
            date_str = ""
        
        formatted_appointments.append({
            "id": str(appt.get('aid')),
            "time": time_str,
            "date": date_str,
            "client": f"{appt.get('first_name', '')} {appt.get('last_name', '')}".strip() or "Unknown Client",
            "service": appt.get('service_name', 'N/A'),
            "duration": appt.get('duration', 60),
            "notes": appt.get('notes', ''),
            "status": "scheduled"
        })
    
    return jsonify(formatted_appointments), 200

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
            "durationMins": appt.get('durationMin', 60),
            "notes": appt.get('notes', ''),
            "status": "scheduled"
        })
    
    return jsonify(formatted_appointments), 200


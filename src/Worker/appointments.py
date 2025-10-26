from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .worker_func import *

appointments = Blueprint("appointments",__name__,url_prefix='/worker')

@appointments.route('/appointments')
@login_required
def list_appointments():
    if(current_user.role != "employee"):
        return jsonify({
            "status": "failure",
            "message": "user is not an employee",
            "user_role": current_user.role
        })
    
    eid = get_eid(current_user.id)
    appointments = get_appointments(eid['eid'])
    if not appointments:
        return jsonify({
            "status": "failure",
            "message": "unable to retrieve upcoming appointments",
            "query_results": appointments
        }) 
    return jsonify({
        "status": "success",
        "message": "retrieved upcoming appointments",
        "query_results": appointments
    })


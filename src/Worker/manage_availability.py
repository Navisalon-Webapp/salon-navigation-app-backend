from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .worker_func import *
from datetime import timedelta

worker_avail = Blueprint("worker_avail",__name__,url_prefix='/worker')

def format_time(t):
    if isinstance(t, timedelta):
        total_seconds = int(t.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    elif isinstance(t, str):
        #HH:MM format
        parts = t.split(":")
        if len(parts) >= 2:
            h, m = int(parts[0]), int(parts[1])
            return f"{h:02d}:{m:02d}"
        return t
    return "09:00"

def serialize_availability(avail_list):
    # Convert datetime objects to HH:MM strings
    serialized = []
    for a in avail_list:
        serialized.append({
            "day": a["day"],
            "start_time": format_time(a["start_time"]),
            "finish_time": format_time(a["finish_time"]),
            "created_at": str(a["created_at"]),
            "updated_at": str(a["updated_at"])
        })
    return serialized

@worker_avail.route('/availability', methods=['GET'])
@login_required
def get_availability():
    # check if user is a salon worker
    if(current_user.role != "employee"):
        return jsonify({
            "status": "Failure",
            "message": "User is not a salon worker",
            "user_role": current_user.role
        }), 403
    
    eid = get_eid(current_user.id)
    print("DEBUG: eid result:", eid)
    curr_avail = get_avail(eid['eid'])
    curr_avail = serialize_availability(curr_avail)
    
    return jsonify({
        "status": "Success",
        "message": "Retrieved worker availability",
        "query_results": curr_avail
    }), 200

@worker_avail.route('/availability', methods=['POST'])
@login_required
def save_availability():    
    # check if user is a salon worker
    if(current_user.role != "employee"):
        return jsonify({
            "status": "Failure",
            "message": "User is not a salon worker",
            "user_role": current_user.role
        }), 403
    
    eid = get_eid(current_user.id)['eid']

    try:
        data=request.get_json()
        week_data = data.get("week")

        if not week_data:
            return jsonify({
                "status": "Failure",
                "message": "No availability data provided"
            }), 400
        
        insert_avail(eid, week_data)

        return jsonify({
            "status": "Success",
            "message": "Worker availability saved to the database"
        }), 200

    except Exception as e:
        print("An error has occured", e)
        return jsonify({
            "status": "Error",
            "message": str(e)
        }), 400
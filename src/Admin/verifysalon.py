from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .queries import *
from .admin_func import *

verifysalon = Blueprint("verifysalon",__name__,url_prefix='admin')

@verifysalon.route('/approve-salon')
@login_required
def verify_salon():
    if(current_user.role != "admin"):
        return jsonify({
            "status": "failure",
            "message": "unauthorized access"
        }), 401
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(update_verify_salon,[data['uid']])
        return jsonify({
            "status": "success",
            "message": "approved salon",
            "User_ID": data['uid']
        }), 200
    except Error as e:
        print(e)
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "Error": e
        }), 400
    
    
    
    
    
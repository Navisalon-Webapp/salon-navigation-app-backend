from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .queries import *
from .admin_func import *

verifysalon = Blueprint("verifysalon",__name__,url_prefix='/admin')

@verifysalon.route('/<int:uid>/approve', methods=['POST'])
@login_required
def verify_salon(uid):
    if(current_user.role != "admin"):
        return jsonify({
            "status": "failure",
            "message": "unauthorized access"
        }), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_verify_salon,(uid,))
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "approved salon",
            "User_ID": [uid]
        }), 200
    except Error as e:
        print(e)
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "Error": e
        }), 400

@verifysalon.route('/<int:uid>/reject', methods=['POST'])
@login_required
def reject_salon(uid):
    if(current_user.role != "admin"):
        return jsonify({
            "status": "failure",
            "message": "unauthorized access"
        }), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(delete_reject_salon,(uid,))
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "rejected salon",
            "User_ID": [uid]
        }), 200
    except Error as e:
        print(e)
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "Error": e
        }), 400

@verifysalon.route('/pending', methods=['GET'])
@login_required
def pending_salons():
    if current_user.role != "admin":
        return jsonify({"message":"unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT business.uid AS id, business.name
            FROM business
            JOIN users ON business.uid = users.uid
            WHERE business.status = 0
        """)
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    
    
    
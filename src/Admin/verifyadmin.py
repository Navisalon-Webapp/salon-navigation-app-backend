from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .queries import *
from .admin_func import *
from helper.utils import checkrole

verifyadmin = Blueprint("verifyadmin",__name__,url_prefix='/admin/admin')

@verifyadmin.route('/<int:uid>/approve', methods=['POST'])
@login_required
def verify_admin(uid):
    if(current_user.role != "admin"):
        return jsonify({
            "status": "failure",
            "message": "unauthorized access"
        }), 401
    try:
        if checkrole(uid) != "admin":
            print("user is not admin")
            return jsonify({
                "status":"failure",
                "message":"user is not admin"
            }), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_verify_admin,(uid,))
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "approved admin",
            "User_ID": [uid]
        }), 200
    except Error as e:
        print(e)
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "Error": e
        }), 400

@verifyadmin.route('/<int:uid>/reject', methods=['DELETE'])
@login_required
def reject_admin(uid):
    if(current_user.role != "admin"):
        return jsonify({
            "status": "failure",
            "message": "unauthorized access"
        }), 401
    try:
        if checkrole(uid) != "admin":
            print("user is not admin")
            return jsonify({
                "status":"failure",
                "message":"user is not admin"
            }), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(delete_admin,(uid,))
        cursor.execute(delete_admin_role, [uid])
        cursor.execute(delete_admin_user, [uid])
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "rejected admin",
            "User_ID": [uid]
        }), 200
    except Error as e:
        print(e)
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "Error": e
        }), 400

@verifyadmin.route('/pending', methods=['GET'])
@login_required
def pending_admins():
    if current_user.role != "admin":
        return jsonify({"message":"unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.uid AS id, concat(u.first_name, ' ', u.last_name) as name
            FROM admin a
            JOIN users u ON a.uid  = u.uid
            WHERE a.status = 0;
        """)
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    
    
    
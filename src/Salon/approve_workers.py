from flask import Blueprint, jsonify, request
from flask_login import login_required
from mysql.connector import Error
from helper.utils import get_db_connection, check_role
import os
from .salon_func import *

approve_workers = Blueprint("approve_workers", __name__, url_prefix="/worker")

@approve_workers.route("/pending/", methods=["GET"])
@login_required
def get_pending_workers():
    if check_role() != 'business':
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"Account is not business"
        }), 403

    db = None
    cursor = None
    try:
        bid = get_curr_bid()

        db = get_db_connection()
        cursor = db.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            SELECT e.eid as id, CONCAT(u.first_name, ' ', u.last_name) AS name, a.email
            FROM employee e
            JOIN users u ON e.uid = u.uid
            JOIN authenticate a ON u.uid = a.uid
            WHERE e.bid=%s AND (e.approved=0 OR e.approved IS NULL or e.approved=FALSE)
        """, (bid,))
        rows = cursor.fetchall()
        print("rows:", rows)
        cursor.close()
        return jsonify(rows), 200
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
        if db:
            db.close()

@approve_workers.route("/<int:eid>/approve", methods=["POST"])
@login_required
def approve_worker(eid):
    if check_role() != 'business':
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"Account is not business"
        }), 403

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        cursor.execute("UPDATE employee SET approved=TRUE WHERE eid=%s", (eid,))
        db.commit()
        return jsonify({"message": "Worker approved"}), 200
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
        if db:
            db.close()

@approve_workers.route("/<int:eid>/reject", methods=["POST"])
@login_required
def reject_worker(eid):
    if check_role() != 'business':
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"Account is not business"
        }), 403

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        cursor.execute("DELETE FROM employee WHERE eid=%s", (eid,))
        db.commit()
        return jsonify({"message": "Worker rejected"})
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
        if db:
            db.close()

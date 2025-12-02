from flask import Blueprint, jsonify, request
from flask_login import login_required
import mysql.connector
import os
from .salon_func import *

approve_workers = Blueprint("approve_workers", __name__, url_prefix="/worker")

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    port=int(os.getenv("DB_PORT")),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

@approve_workers.route("/pending/", methods=["GET"])
@login_required
def get_pending_workers():
    bid = get_curr_bid()
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
    return jsonify(rows)

@approve_workers.route("/<int:eid>/approve", methods=["POST"])
@login_required
def approve_worker(eid):
    cursor = db.cursor(buffered=True)
    cursor.execute("UPDATE employee SET approved=TRUE WHERE eid=%s", (eid,))
    db.commit()
    return jsonify({"message": "Worker approved"})

@approve_workers.route("/<int:eid>/reject", methods=["POST"])
@login_required
def reject_worker(eid):
    cursor = db.cursor(buffered=True)
    cursor.execute("DELETE FROM employee WHERE eid=%s", (eid,))
    db.commit()
    return jsonify({"message": "Worker rejected"})

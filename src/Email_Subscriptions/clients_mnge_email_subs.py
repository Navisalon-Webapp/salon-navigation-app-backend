from flask import request, jsonify, Blueprint
from flask_cors import CORS
from src.extensions import scheduler
import mysql.connector
from helper.utils import get_curr_cid
from flask_login import login_required
from dotenv import load_dotenv
import os

load_dotenv()

manage_email_sub = Blueprint('manage_email_sub', __name__)





def get_db_connection():
    """Create a new database connection"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


#clients can manage promotion email subscriptions
@manage_email_sub.route("/api/clients/manage-email-subs", methods=["POST"])
@login_required
def manage_promotion_subscription():
    data = request.get_json()
    # id = data.get("cid")
    promotion : bool = data['promotion']
    cid = get_curr_cid()

    # if not id:
    #     return jsonify({"error": "User ID (uid) is required"}), 400
    
    db = None
    cursor=None
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = f"""
        update email_subscription
        set promotion = {promotion}
        where cid = %s;
        """
        cursor.execute(query, (cid,))
        db.commit()

        # if cursor.rowcount == 0:
        #     return jsonify({"message": "No customer found with that ID."}), 404
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        if db:
            db.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
    
    return jsonify({"message": "Promotion email subscription preferences updated successfully."}), 200 

#clients can manage appointment reminder email subscriptions
@manage_email_sub.route("/api/clients/manage-appt-reminder-subs", methods=["POST"])
@login_required
def manage_appt_reminder_subscription():
    data = request.get_json()
    # id = data.get("cid")
    # if not id:
    #     return jsonify({"error": "User ID (uid) is required"}), 400
    appt : bool = data['appointment']
    cid = get_curr_cid()
    
    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = f"""
        update email_subscription
        set appointment = {appt}
        where cid = %s;
        """
        cursor.execute(query, (cid,))
        db.commit()

        # if cursor.rowcount == 0:
        #     return jsonify({"message": "No customer found with that ID."}), 404
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        if db:
            db.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    if not appt:
        jobs = scheduler.get_jobs()
        for j in jobs:
            job_id = j.id
            split_id = job_id.split(":")
            c = split_id[2]
            if str(cid) == c:
                scheduler.remove_job(job_id)

    
    return jsonify({"message": "Appointment reminder email subscription preferences updated successfully."}), 200
        


    
    
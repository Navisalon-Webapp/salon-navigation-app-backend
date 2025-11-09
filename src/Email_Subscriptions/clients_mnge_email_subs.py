from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
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
def manage_promotion_subscription():
    data = request.get_json()
    id = data.get("cid")

    if not id:
        return jsonify({"error": "User ID (uid) is required"}), 400
    
    db = None
    cursor=None
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = """
        update email_subscription
        set promotion = false
        where uid = %s;
        """
        cursor.execute(query, (id,))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No customer found with that ID."}), 404
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
def manage_appt_reminder_subscription():
    data = request.get_json()
    id = data.get("cid")
    if not id:
        return jsonify({"error": "User ID (uid) is required"}), 400
    
    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()

        query = """
        update email_subscription
        set appointment = false
        where uid = %s;
        """
        cursor.execute(query, (id,))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No customer found with that ID."}), 404
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
    
    return jsonify({"message": "Appointment reminder email subscription preferences updated successfully."}), 200
        


    
    
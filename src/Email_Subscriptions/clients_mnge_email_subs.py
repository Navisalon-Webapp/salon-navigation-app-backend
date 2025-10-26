from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

manage_email_sub = Blueprint('manage_email_sub', __name__)





db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()


#clients can manage promotion email subscriptions
@manage_email_sub.route("/api/clients/manage-email-subs", methods=["POST"])
def manage_promotion_subscription():
    data = request.get_json()
    customer_id = data.get("cid")

    if not customer_id:
        return jsonify({"error": "Customer ID (cid) is required"}), 400
    
    try:
        query = """
        update email_subscription
        set promotion = false
        where cid = %s;
        """
        cursor.execute(query, (customer_id,))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No customer found with that ID."}), 404
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database error occurred."}), 500
    
    return jsonify({"message": "Promotion email subscription preferences updated successfully."}), 200 

#clients can manage appointment reminder email subscriptions
@manage_email_sub.route("/api/clients/manage-appt-reminder-subs", methods=["POST"])
def manage_appt_reminder_subscription():
    data = request.get_json()
    customer_id = data.get("cid")
    if not customer_id:
        return jsonify({"error": "Customer ID (cid) is required"}), 400
    try:
        query = """
        update email_subscription
        set appointment = false
        where cid = %s;
        """
        cursor.execute(query, (customer_id,))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No customer found with that ID."}), 404
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database error occurred."}), 500
    return jsonify({"message": "Appointment reminder email subscription preferences updated successfully."}), 200
        


    
    
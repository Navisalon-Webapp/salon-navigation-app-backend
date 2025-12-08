from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from src.extensions import scheduler
from src.Appointments.app_func import get_cid_for_aid
from dotenv import load_dotenv
import os

load_dotenv()

cancel_appts = Blueprint('cancel_appts', __name__)





db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    port=int(os.getenv("DB_PORT")),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()


#clients can cancel appointments
@cancel_appts.route("/api/user/cancel-appt", methods=["POST"])
def cancel_appt():
    data = request.get_json()
    appointment_id = data.get("aid")
    if not appointment_id:
        return jsonify({"error": "Appointment ID (aid) is required"}), 400

    try:
        cid=get_cid_for_aid(cursor, appointment_id)
        query = "DELETE FROM appointments WHERE aid = %s"
        cursor.execute(query, (appointment_id,))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No appointment found with that ID."}), 404
        
        if scheduler.get_job(f"Appointment:{appointment_id}:{cid}"):
            scheduler.remove_job(f"Appointment:{appointment_id}:{cid}")

        return jsonify({"message": "Appointment cancelled successfully."}), 200

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database error occurred."}), 500
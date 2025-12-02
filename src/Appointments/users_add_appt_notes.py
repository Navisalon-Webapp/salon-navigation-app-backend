from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

add_notes = Blueprint('add_note', __name__)





db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    port=int(os.getenv("DB_PORT")),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()


#notes can be added to appointments
@add_notes.route("/api/user/add-notes", methods=["POST"])
def appt_notes():
    data = request.get_json()
    appointment_id = data.get("aid")
    notes = data.get("notes")
    if not appointment_id or not notes:
        return jsonify({"error": "Both 'aid' and 'notes' are required"}), 400

    try:
        query = """
            UPDATE appointments
            SET notes = %s
            WHERE aid = %s;
        """
        cursor.execute(query, (notes, appointment_id))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No notes were added. Either the appointment doesn't exist or notes already exist."}), 404

        return jsonify({"message": "Notes added to appointment successfully."}), 201

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": "Database error occurred."}), 500
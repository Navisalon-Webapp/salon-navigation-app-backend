from flask import Blueprint, request, jsonify
from flask_login import login_required
import mysql.connector
import os
from .salon_func import *

manage_services = Blueprint("manage_services", __name__, url_prefix="/services")

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

# Get all services a business offers
@manage_services.route("/", methods=["GET"])
@login_required
def get_services():
    try:
        bid = get_curr_bid()
        cursor = db.cursor()
        cursor.execute(
            "SELECT sid, name, price, durationMin FROM services WHERE bid = %s", (bid,)
        )
        rows = cursor.fetchall()
        cursor.close()

        services = [
            {"id": sid, "name": name, "durationMin": durationMin, "priceUsd": float(price)}
            for (sid, name, price, durationMin) in rows
        ]
        return jsonify(services), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Add a new service
@manage_services.route("/", methods=["POST"])
@login_required
def add_service():
    try:
        bid = get_curr_bid()
        data = request.get_json()
        name = data.get("name")
        durationMin = data.get("durationMin")
        price = data.get("priceUsd")

        if not name or price is None:
            return jsonify({"error": "Missing fields"}), 400

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO services (name, price, bid, durationMin) VALUES (%s, %s, %s, %s)",
            (name, price, bid, durationMin),
        )
        db.commit()
        sid = cursor.lastrowid
        cursor.close()

        return jsonify({
            "id": sid,
            "name": name,
            "durationMin": durationMin,
            "priceUsd": float(price),
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Update a service
@manage_services.route("/<int:sid>", methods=["PUT"])
@login_required
def update_service(sid):
    try:
        data = request.get_json()
        name = data.get("name")
        durationMin = data.get("durationMin")
        price = data.get("priceUsd")

        cursor = db.cursor()
        cursor.execute(
            "UPDATE services SET name = %s, price = %s , durationMin = %s WHERE sid = %s",
            (name, price, durationMin, sid),
        )
        db.commit()
        cursor.close()

        return jsonify({"message": "Service updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete a service
@manage_services.route("/<int:sid>", methods=["DELETE"])
@login_required
def delete_service(sid):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM services WHERE sid = %s", (sid,))
        db.commit()
        cursor.close()

        return jsonify({"message": "Service deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

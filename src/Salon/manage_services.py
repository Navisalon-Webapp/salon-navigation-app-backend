from flask import Blueprint, request, jsonify
from flask_login import login_required
from mysql.connector import Error
from helper.utils import get_db_connection, check_role
import os
from .salon_func import *

manage_services = Blueprint("manage_services", __name__, url_prefix="/services")

# Get all services a business offers
@manage_services.route("/", methods=["GET"])
@login_required
def get_services():
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
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "SELECT sid, name, price, durationMin FROM services WHERE bid = %s", (bid,)
        )
        rows = cursor.fetchall()

        services = [
            {"id": sid, "name": name, "durationMin": durationMin, "priceUsd": float(price)}
            for (sid, name, price, durationMin) in rows
        ]
        return jsonify(services), 200
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


# Add a new service
@manage_services.route("/", methods=["POST"])
@login_required
def add_service():
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
        data = request.get_json()
        name = data.get("name")
        durationMin = data.get("durationMin")
        price = data.get("priceUsd")

        if not name or price is None:
            return jsonify({"error": "Missing fields"}), 400

        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "INSERT INTO services (name, price, bid, durationMin) VALUES (%s, %s, %s, %s)",
            (name, price, bid, durationMin),
        )
        db.commit()
        sid = cursor.lastrowid

        return jsonify({
            "id": sid,
            "name": name,
            "durationMin": durationMin,
            "priceUsd": float(price),
        }), 201

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


# Update a service
@manage_services.route("/<int:sid>", methods=["PUT"])
@login_required
def update_service(sid):
    if check_role() != 'business':
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"Account is not business"
        }), 403

    db = None
    cursor = None
    try:
        data = request.get_json()
        name = data.get("name")
        durationMin = data.get("durationMin")
        price = data.get("priceUsd")

        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "UPDATE services SET name = %s, price = %s , durationMin = %s WHERE sid = %s",
            (name, price, durationMin, sid),
        )
        db.commit()

        return jsonify({"message": "Service updated"}), 200
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


# Delete a service
@manage_services.route("/<int:sid>", methods=["DELETE"])
@login_required
def delete_service(sid):
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
        cursor.execute("DELETE FROM services WHERE sid = %s", (sid,))
        db.commit()

        return jsonify({"message": "Service deleted"}), 200
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

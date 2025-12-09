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
            "SELECT s.sid, s.name, s.price, s.duration, s.description, sc.name AS category, " \
            "COALESCE(GROUP_CONCAT(CONCAT(e.eid, '::', u.first_name, ' ', u.last_name) SEPARATOR '||'), '') AS workers " \
            "FROM services s " \
            "JOIN service_categories sc ON s.cat_id = sc.cat_id " \
            "LEFT JOIN employee_services es ON s.sid = es.sid " \
            "LEFT JOIN employee e ON es.eid = e.eid " \
            "LEFT JOIN users u ON e.uid = u.uid " \
            "WHERE s.bid = %s " \
            "GROUP BY s.sid " \
            "ORDER BY s.name ASC", (bid,)
        )
        rows = cursor.fetchall()
        cursor.close()

        services = []
        for (sid, name, price, duration, description, category, workers_agg) in rows:
            workers = []
            if workers_agg:
                for part in workers_agg.split("||"):
                    if not part:
                        continue
                    # part looks like "eid::Full Name"
                    try:
                        eid_str, full_name = part.split("::", 1)
                        workers.append({"eid": int(eid_str), "name": full_name})
                    except Exception:
                        continue
            services.append({
                "id": sid,
                "name": name,
                "priceUsd": float(price) if price is not None else None,
                "duration": duration,
                "description": description,
                "category": category,
                "workers": workers
            })
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
        duration = data.get("duration")
        price = data.get("priceUsd")
        cat_id = data.get("cat_id")
        category = data.get("category")
        description = data.get("description")
        workers = data.get("workers") or []

        print("Trying with params: (bid)", bid, ", (name) ", name, ", (cat_id) ", cat_id, ", (category) ", category, ", (price) ", price, ", (duration) ", duration, ", (desc) ", description)
        print("not name", not name)
        print("price is None", price is None)
        print("duration is None", duration is None)
        print("category is None", category is None)

        if not name or price is None or duration is None or category is None:
            return jsonify({"error": "Missing required fields"}), 400

        db = get_db_connection()
        cursor = db.cursor(buffered=True)

        try:
            cat_id = get_or_create_category(cursor, cat_id, category)
        except ValueError as ve:
            cursor.close()
            return jsonify({"Error getting or creating service category": str(ve)}), 400

        print("Trying with params: ", bid, name, cat_id, price, duration, description)
        cursor.execute(
            "INSERT INTO services (bid, name, cat_id, price, duration, description) VALUES (%s, %s, %s, %s, %s, %s)",
            (bid, name, cat_id, price, duration, description),
        )
        sid = cursor.lastrowid

        if workers:
            assigned = [(int(w), sid) for w in workers]
            cursor.executemany(
                "INSERT INTO employee_services (eid, sid) VALUES (%s, %s)", assigned
            )

        db.commit()
        cursor.close()

        return jsonify({
            "id": sid,
            "name": name,
            "duration": duration,
            "priceUsd": float(price),
            "category": category,
            "description": description,
            "workers": [{"eid": int(w)} for w in workers]
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
        duration = data.get("duration")
        price = data.get("priceUsd")
        cat_id = data.get("cat_id")
        category = data.get("category")
        description = data.get("description")
        workers = data.get("workers") or []

        db = get_db_connection()
        cursor = db.cursor(buffered=True)

        try:
            cat_id = get_or_create_category(cursor, cat_id, category)
        except ValueError as ve:
            cursor.close()
            return jsonify({"Error getting or creating service category": str(ve)}), 400

        cursor.execute(
            "UPDATE services SET name = %s, price = %s , duration = %s, cat_id = %s, description = %s WHERE sid = %s",
            (name, price, duration, cat_id, description, sid),
        )

        cursor.execute(
            "DELETE FROM employee_services WHERE sid = %s", (sid,)
        )

        if workers:
            assigned = [(int(w), sid) for w in workers]
            cursor.executemany(
                "INSERT INTO employee_services (eid, sid) VALUES (%s, %s)", assigned
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

# Get service category options
@manage_services.route("/categories", methods=["GET"])
@login_required
def get_categories():
    try:
        db = get_db_connection()
        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT cat_id, name FROM service_categories ORDER BY name ASC")
        rows = cursor.fetchall()
        cursor.close()
        cats = [{"id": cid, "name": name} for (cid, name) in rows]
        return jsonify(cats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get salon employees to assign to services
@manage_services.route("/employees", methods=["GET"])
@login_required
def get_employees_for_business():
    try:
        db = get_db_connection()
        bid = get_curr_bid()
        cursor = db.cursor(buffered=True)
        cursor.execute("""
            SELECT e.eid, u.first_name, u.last_name
            FROM employee e
            JOIN users u ON e.uid = u.uid
            WHERE e.bid = %s AND e.approved = TRUE
            ORDER BY u.first_name, u.last_name
        """, (bid,))
        rows = cursor.fetchall()
        cursor.close()
        employees = [{"eid": eid, "name": f"{first} {last}"} for (eid, first, last) in rows]
        return jsonify(employees), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
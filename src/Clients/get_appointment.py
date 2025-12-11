"""Endpoint for retrieving customer appointment details with payment totals."""

from __future__ import annotations

import os

from flask import Blueprint, jsonify
from flask_login import current_user, login_required
import mysql.connector
from dotenv import load_dotenv

from helper.utils import check_role

load_dotenv()

get_appointment = Blueprint("get_appointment", __name__)


def get_db() -> mysql.connector.MySQLConnection | None:
    """Create a new database connection using environment credentials."""

    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            port=int(os.getenv("DB_PORT")),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    except mysql.connector.Error as err:
        print(f"Error: Database could not connect. : {err}")
        return None


@get_appointment.route("/api/clients/appointment/<int:aid>", methods=["GET"])
@login_required
def get_appointment_details(aid: int):
    """Return appointment details for the logged-in customer including payment summary."""

    db = None
    cursor = None

    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500

        cursor = db.cursor(dictionary=True)

        query = (
            "SELECT "
            " a.aid, a.cid, a.eid, a.sid, a.start_time, a.expected_end_time, a.end_time, "
            " s.name AS service_name, s.price AS service_price, s.duration AS service_duration,"
            " u_employee.first_name AS employee_first_name,"
            " u_employee.last_name AS employee_last_name,"
            " u_employee.uid AS employee_user_uid,"
            " u_customer.first_name AS customer_first_name,"
            " u_customer.last_name AS customer_last_name,"
            " u_customer.uid AS customer_uid,"
            " b.name AS business_name, b.bid, b.deposit_rate, b.uid AS business_owner_uid,"
            " addr.street, addr.city, addr.state, addr.country, addr.zip_code "
            "FROM appointments a "
            "JOIN services s ON a.sid = s.sid "
            "JOIN employee e ON a.eid = e.eid "
            "JOIN users u_employee ON e.uid = u_employee.uid "
            "JOIN customers c ON a.cid = c.cid "
            "JOIN users u_customer ON c.uid = u_customer.uid "
            "JOIN business b ON e.bid = b.bid "
            "LEFT JOIN addresses addr ON b.aid = addr.aid "
            "WHERE a.aid = %s"
        )

        cursor.execute(query, (aid,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "Appointment not found."}), 404

        user_id = str(current_user.id)
        allowed_ids = {
            str(result.get("customer_uid")),
            str(result.get("employee_user_uid")),
            str(result.get("business_owner_uid")),
        }

        if user_id not in allowed_ids:
            try:
                if check_role() != "admin":
                    return jsonify({"message": "Unauthorized."}), 403
            except Exception as exc:
                print(f"Role verification failed: {exc}")
                return jsonify({"message": "Unauthorized."}), 403

        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) AS paid_amount "
            "FROM transactions WHERE aid = %s AND payment_method_id IS NOT NULL",
            (aid,),
        )
        payment_row = cursor.fetchone() or {"paid_amount": 0}

        paid_amount = float(payment_row.get("paid_amount") or 0)
        service_price = float(result.get("service_price") or 0)
        deposit_rate = float(result.get("deposit_rate") or 0)
        deposit_required = round(service_price * deposit_rate, 2)
        deposit_outstanding = max(round(deposit_required - paid_amount, 2), 0.0)
        balance_due = max(round(service_price - paid_amount, 2), 0.0)

        appointment_data = {
            "id": result.get("aid"),
            "customer_id": result.get("cid"),
            "employee_id": result.get("eid"),
            "service_id": result.get("sid"),
            "business_id": result.get("bid"),
            "client": f"{result.get('customer_first_name')} {result.get('customer_last_name')}",
            "worker": f"{result.get('employee_first_name')} {result.get('employee_last_name')}",
            "service": result.get("service_name"),
            "price": service_price,
            "duration": result.get("service_duration"),
            "date": result["start_time"].strftime("%b %d, %Y") if result.get("start_time") else "",
            "time": result["start_time"].strftime("%I:%M %p") if result.get("start_time") else "",
            "start_time": result["start_time"].isoformat() if result.get("start_time") else None,
            "expected_end_time": result["expected_end_time"].isoformat()
            if result.get("expected_end_time")
            else None,
            "end_time": result["end_time"].isoformat() if result.get("end_time") else None,
            "status": "Completed" if result.get("end_time") else "Scheduled",
            "business_name": result.get("business_name"),
            "address": {
                "street": result.get("street"),
                "city": result.get("city"),
                "state": result.get("state"),
                "country": result.get("country"),
                "zip_code": result.get("zip_code"),
            },
            "payments": {
                "deposit_rate": deposit_rate,
                "deposit_required": deposit_required,
                "deposit_outstanding": deposit_outstanding,
                "total_paid": round(paid_amount, 2),
                "balance_due": balance_due,
            },
        }

        return jsonify(appointment_data), 200

    except mysql.connector.Error as err:
        print(f"Error fetching appointment: {err}")
        return jsonify({"message": "Failed to fetch appointment details."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

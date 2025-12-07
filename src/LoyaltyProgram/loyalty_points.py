"""Blueprint endpoints for loyalty point earning and redemption."""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request
from flask_login import login_required
from mysql.connector import Error

from helper.utils import check_role, get_curr_cid, get_db_connection
from .loyalty_service import award_points_for_visit, redeem_points

loyalty_points = Blueprint("loyalty_points", __name__, url_prefix="/api/loyalty")


def _parse_int(value: Any, field: str) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be an integer")


@loyalty_points.route("/earn", methods=["POST"])
@login_required
def earn_loyalty_points():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    aid = _parse_int(payload.get("appointmentId") or payload.get("aid"), "appointmentId")
    if aid is None:
        return jsonify({"status": "failure", "message": "appointmentId is required"}), 400

    points_override_raw = payload.get("points")
    points_override: Optional[int] = None
    if points_override_raw is not None:
        points_override = _parse_int(points_override_raw, "points")
        if points_override is not None and points_override < 0:
            return jsonify({"status": "failure", "message": "points must be non-negative"}), 400

    role = check_role()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "failure", "message": "database connection failed"}), 500

        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT a.cid, s.bid, s.price
            FROM appointments a
            JOIN services s ON a.sid = s.sid
            WHERE a.aid = %s
            """,
            (aid,),
        )
        appt = cursor.fetchone()
        if not appt:
            return jsonify({"status": "failure", "message": "appointment not found"}), 404

        appointment_cid = appt["cid"]
        bid = appt["bid"]
        amount = appt["price"]

        if role == "customer":
            current_cid = get_curr_cid()
            if current_cid != appointment_cid:
                return jsonify({"status": "failure", "message": "appointment does not belong to current customer"}), 403
        elif role not in {"owner", "business", "employee", "admin"}:
            return jsonify({"status": "failure", "message": "user not authorized to award loyalty"}), 403

        result = award_points_for_visit(
            conn,
            aid=aid,
            cid=appointment_cid,
            bid=bid,
            amount=amount,
            explicit_points=points_override,
            source="visit",
        )

        message = "loyalty points awarded" if result.get("awarded") else "loyalty points already awarded"
        return (
            jsonify(
                {
                    "status": "success",
                    "message": message,
                    "data": result,
                }
            ),
            200,
        )
    except ValueError as exc:
        return jsonify({"status": "failure", "message": str(exc)}), 400
    except Error as exc:
        return jsonify({"status": "failure", "message": f"database error: {exc}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@loyalty_points.route("/redeem", methods=["POST"])
@login_required
def redeem_loyalty_points():
    role = check_role()
    if role != "customer":
        return jsonify({"status": "failure", "message": "only customers can redeem loyalty points"}), 403

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    bid = _parse_int(payload.get("bid"), "bid")
    points = _parse_int(payload.get("points"), "points")

    if bid is None or points is None:
        return jsonify({"status": "failure", "message": "bid and points are required"}), 400

    if points <= 0:
        return jsonify({"status": "failure", "message": "points must be greater than zero"}), 400

    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "failure", "message": "database connection failed"}), 500

        cid = get_curr_cid()
        result = redeem_points(conn, cid=cid, bid=bid, points=points)
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "points redeemed",
                    "data": result,
                }
            ),
            200,
        )
    except ValueError as exc:
        return jsonify({"status": "failure", "message": str(exc)}), 400
    except Error as exc:
        return jsonify({"status": "failure", "message": f"database error: {exc}"}), 500
    finally:
        if conn:
            conn.close()

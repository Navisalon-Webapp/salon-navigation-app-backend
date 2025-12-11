from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_login import login_required

import mysql.connector
from helper.utils import check_role, get_curr_bid, get_db_connection


deposit_rate = Blueprint("deposit_rate", __name__, url_prefix="/business")


@deposit_rate.route("/deposit/<int:bid>", methods=["GET"])
def get_deposit(bid: int):
    if not bid:
        return (
            jsonify({"status": "failure", "message": "Business id is required"}),
            400,
        )

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT deposit_rate FROM business WHERE bid = %s",
            [bid],
        )
        result = cursor.fetchone()
        if not result:
            return (
                jsonify({
                    "status": "failure",
                    "message": "Business not found",
                }),
                404,
            )

        return (
            jsonify({
                "status": "success",
                "message": "Retrieved business deposit rate",
                "business_id": bid,
                "deposit_rate": float(result.get("deposit_rate") or 0),
            }),
            200,
        )
    except mysql.connector.Error as exc:  # type: ignore[name-defined]
        print(f"Database Error {exc}")
        return (
            jsonify({
                "status": "failure",
                "message": "Database Error",
                "error": str(exc),
            }),
            500,
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@deposit_rate.route("/set-deposit", methods=["PATCH"])
@login_required
def set_deposit():
    try:
        if check_role() != "business":
            return (
                jsonify({
                    "status": "failure",
                    "message": "User is not a business account",
                }),
                401,
            )
        bid = get_curr_bid()
    except ValueError as exc:
        return (
            jsonify({"status": "failure", "message": str(exc)}),
            401,
        )

    payload = request.get_json() or {}
    raw_rate = payload.get("deposit_rate")
    if raw_rate is None:
        return (
            jsonify({
                "status": "failure",
                "message": "deposit_rate is required",
            }),
            400,
        )

    try:
        rate = Decimal(str(raw_rate))
    except (InvalidOperation, TypeError):
        return (
            jsonify({
                "status": "failure",
                "message": "deposit_rate must be a numeric value",
            }),
            400,
        )

    if rate < 0 or rate > 1:
        return (
            jsonify({
                "status": "failure",
                "message": "deposit_rate must be between 0 and 1",
            }),
            400,
        )

    normalized_rate = float(rate.quantize(Decimal("0.01")))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE business SET deposit_rate = %s WHERE bid = %s",
            [normalized_rate, bid],
        )
        conn.commit()
        return (
            jsonify({
                "status": "success",
                "message": "Updated business deposit rate",
                "business_id": bid,
                "deposit_rate": normalized_rate,
            }),
            200,
        )
    except mysql.connector.Error as exc:  # type: ignore[name-defined]
        print(f"Database Error {exc}")
        if conn:
            conn.rollback()
        return (
            jsonify({
                "status": "failure",
                "message": "Database Error",
                "error": str(exc),
            }),
            500,
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
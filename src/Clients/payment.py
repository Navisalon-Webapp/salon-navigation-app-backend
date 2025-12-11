from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *

payment = Blueprint("payment", __name__, url_prefix="/payment")

def _assert_current_user(uid: str) -> int:
    """Ensure the authenticated user is requesting their own payment data."""
    if not current_user.is_authenticated:
        raise PermissionError("Authentication required")

    try:
        uid_int = int(uid)
    except (TypeError, ValueError):
        raise PermissionError("Invalid user id")

    current_uid = str(current_user.id)
    if current_uid != str(uid_int):
        try:
            if check_role() != "admin":
                raise PermissionError("Not authorised to view this payment information")
        except Exception as exc:
            print(f"Role check failed: {exc}")
            raise PermissionError("Not authorised to view this payment information")

    return uid_int

@payment.route('/<uid>', methods=['GET'])
@login_required
def payment_information(uid):
    conn = None
    cursor = None
    try:
        uid_int = _assert_current_user(uid)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query_payment_information = """
            select id, payment_type, cardholder_name, card_number, exp_month, exp_year
            from payment_information
            where uid = %s;
        """
        cursor.execute(query_payment_information, [uid_int])
        results = cursor.fetchall()
        sanitized = []
        for row in results:
            last4 = row.get("card_number", "")
            last4 = last4[-4:] if last4 else ""
            sanitized.append({
                "id": row.get("id"),
                "payment_type": row.get("payment_type"),
                "cardholder_name": row.get("cardholder_name"),
                "card_last4": last4,
                "exp_month": row.get("exp_month"),
                "exp_year": row.get("exp_year"),
            })
        return jsonify(sanitized)
    except PermissionError as auth_err:
        return jsonify({
            "status": "failure",
            "message": str(auth_err)
        }), 403
    except Error as e:
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
        if conn:
            conn.close()

@payment.route('/new/<uid>', methods=['POST'])
@login_required
def insert_payment(uid):
    data = request.get_json() or {}
    payment_type = (data.get('payment_type') or '').strip().lower()
    cardholder_name = (data.get('cardholder_name') or '').strip()
    card_number = (data.get('card_number') or '').replace(' ', '')
    cvv = (data.get('cvv') or '').strip()
    exp_month = (data.get('exp_month') or '').strip()
    exp_year = (data.get('exp_year') or '').strip()

    if not payment_type or not card_number or not cardholder_name or not cvv or not exp_month or not exp_year:
        print("Missing parameters")
        return jsonify({
            "status":"failure",
            "message":"Missing parameters"
        }), 400

    uid_int = _assert_current_user(uid)
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_payment_info = """
            insert into payment_information (uid, payment_type, cardholder_name, card_number, cvv, exp_month, exp_year)
            values (%s, %s, %s, %s, %s, %s, %s)
        """
        param = [uid_int, payment_type, cardholder_name, card_number, cvv, exp_month, exp_year]
        cursor.execute(insert_payment_info, param)
        pay_id = cursor.lastrowid
        conn.commit()
        last4 = card_number[-4:] if card_number else ""
        return jsonify({
            "status":"success",
            "message":"created new payment method for user",
            "user_id": uid_int,
            "payment_id": pay_id,
            "payment_type": payment_type,
            "cardholder_name": cardholder_name,
            "card_last4": last4,
            "exp_month": exp_month,
            "exp_year": exp_year
        })
    except PermissionError as auth_err:
        return jsonify({
            "status": "failure",
            "message": str(auth_err)
        }), 403
    except Error as e:
        print(f"Database Error {e}")
        if conn:
            conn.rollback()
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        if conn:
            conn.rollback()
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@payment.route("/remove/<id>", methods=['DELETE'])
@login_required
def remove_payment(id):
    conn = None
    cursor = None
    try:
        uid_int = current_user.id
        conn = get_db_connection()
        cursor = conn.cursor()
        delete_payment_information = """
            delete from payment_information
            where id = %s and uid = %s
        """
        cursor.execute(delete_payment_information, [id, uid_int])
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({
                "status":"failure",
                "message":"payment method not found"
            }), 404
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"payment deleted"
        })
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
        if conn:
            conn.close()


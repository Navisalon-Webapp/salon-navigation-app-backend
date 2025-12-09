from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *

payment = Blueprint("payment", __name__, url_prefix="/payment")

@payment.route('/<uid>', methods=['GET'])
def payment_information(uid):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query_payment_information = """
            select id, payment_type, cardholder_name, card_number, cvv, exp_month, exp_year
            from payment_information
            where uid = %s;
        """
        cursor.execute(query_payment_information, [uid])
        results = cursor.fetchall()
        return jsonify(results)
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

@payment.route('/new/<uid>', methods=['POST'])
def insert_payment(uid):
    data = request.get_json()
    payment_type = data['payment_type']
    cardholder_name = data['cardholder_name']
    card_number = data['card_number']
    cvv = data['cvv']
    exp_month = data['exp_month']
    exp_year = data['exp_year']

    if not payment_type or not card_number or not cardholder_name or not cvv or not exp_month or not exp_year:
        print("Missing parameters")
        return jsonify({
            "status":"success",
            "message":"Missing parameters"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_payment_info = """
            insert into payment_information (uid, payment_type, cardholder_name, card_number, cvv, exp_month, exp_year)
            values (%s, %s, %s, %s, %s, %s, %s)
        """
        param = [uid, payment_type, cardholder_name, card_number, cvv, exp_month, exp_year]
        cursor.execute(insert_payment_info, param)
        pay_id = cursor.lastrowid
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"created new payment method for user",
            "User ID": uid,
            "Payment ID": pay_id
        })
    except mysql.connector.Error as e:
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
def remove_payment(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        delete_payment_information = """
            delete from payment_information
            where id = %s
        """
        cursor.execute(delete_payment_information, [id])
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


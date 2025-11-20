from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *

deposit = Blueprint("deposit", __name__, url_prefix="/deposit")

@deposit.route('/appointment', methods=['POST'])
@login_required
def appointment_deposit():
    data = request.get_json()
    aid = data['aid'] if data['aid'] else None
    payment_id = data['payment_id'] if data['payment_id'] else None
    if not aid or not payment_id:
        print("Missing parameters")
        return jsonify({
            "status":"success",
            "message":"Missing parameters"
        }), 400
    uid = current_user.id
    if check_role(uid) != 'customer':
        print("Wrong account type")
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 401
    cid = get_curr_cid()

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("select cid from appointments where aid = %s;", [aid])
        result = cursor.fetchone()
        appt_cid = result['cid']
        if cid != appt_cid:
            return jsonify({
                "status":"failure",
                "message":"customer did not make this appointment"
            }), 401
        query_business_deposit = """
            select b.deposit_rate, s.price, b.bid
            from appointments a
            join services s on a.sid=s.sid
            join business b on s.bid=b.bid
            where a.aid = %s;
        """
        cursor.execute(query_business_deposit, [aid])
        result = cursor.fetchone()
        deposit_rate = result['deposit_rate']
        price = result['price']
        bid = result['bid']
        deposit = price * deposit_rate
        insert_transaction_deposit = """
            insert into transactions (cid, bid, aid, amount, payment_method_id)
            values (%s, %s, %s, %s, %s);
        """
        param = [cid, bid, aid, deposit, payment_id]
        cursor.execute(insert_transaction_deposit, param)
        trans_id = cursor.lastrowid
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"payment deposited for appointment",
            "deposit": deposit,
            "transaction ID": trans_id
        }), 200
        
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

@deposit.route('/payment/<uid>', methods=['GET'])
def payment_information(uid):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query_payment_information = """
            select id, payment_type, card_number
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

@deposit.route('/new-payment/<uid>', methods=['POST'])
def insert_payment(uid):
    data = request.get_json()
    payment_type = data['payment_type'] if data['payment_type'] else None
    card_number = data['card_number'] if data['card_number'] else None
    if not payment_type or not card_number:
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
            insert into payment_information (uid, payment_type, card_number)
            values (%s, %s, %s)
        """
        param = [uid, payment_type, card_number]
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
    
    
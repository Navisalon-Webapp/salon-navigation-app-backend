from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *

deposit_rate = Blueprint("deposit_rate", __name__, url_prefix='/business')

@deposit_rate.route('/deposit/<int:bid>', methods=['GET'])
def get_deposit(bid):
    if not bid or not isinstance(bid, int):
        print("incorrect or missing parameter")
        return jsonify({
            "status":"failure",
            "message":"incorrect missing parameter"
        }), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query_business_deposit = """
            select deposit_rate
            from business
            where bid = %s;
        """
        cursor.execute(query_business_deposit, [bid])
        result = cursor.fetchone()
        return jsonify({
            "status":"success",
            "message":"retrieved business deposit rate",
            "business id":bid,
            "deposit rate": result['deposit_rate']
        }), 200
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

@deposit_rate.route('/set-deposit', methods=['PATCH'])
@login_required
def set_deposit():
    bid = get_curr_bid()
    if(check_role() != 'business' or not bid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"User is not a business account",
        }), 401
    
    data = request.get_json()
    deposit_rate = data['deposit_rate'] if data['deposit_rate'] else None
    if not deposit_rate or not isinstance(deposit_rate, float):
        print("incorrect or missing parameter")
        return jsonify({
            "status":"failure",
            "message":"incorrect or missing parameter"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        update_business_deposit = """
            update business
            set deposit_rate = %s
            where bid = %s;
        """
        cursor.execute(update_business_deposit, [deposit_rate, bid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"updated business deposit",
            "business id":bid
        }), 200
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
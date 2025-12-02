from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from datetime import datetime, time
from helper.utils import *

operation = Blueprint('operation', __name__, url_prefix='/operation')

@operation.route('/<uid>', methods=['GET'])
def get_hours(uid):
    """list business hours"""
    if(checkrole(uid) != 'business'):
        print("uid provided is not a business account")
        return jsonify({
            "status":"failure",
            "message":"uid provided is not a business account"
        }), 401
    bid = get_bid_from_uid(uid)
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query_hours_of_operation = """
            select id, day, open_time, close_time, is_closed
            from hours_of_operation
            where bid=%s;
        """
        cursor.execute(query_hours_of_operation,[bid])
        results = cursor.fetchall()
        for h in results:
            h['open_time'] = (datetime.min + h['open_time']).time().isoformat()
            h['close_time'] = (datetime.min + h['close_time']).time().isoformat()
        return jsonify({
            "status":"success",
            "message":"retrieved hours of operation",
            "operation_hours": results
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

@operation.route('/', methods=['POST'])
@login_required
def insert_hours():
    """add business hours for particular day"""
    if(check_role() != 'business'):
        print("uid provided is not a business account")
        return jsonify({
            "status":"failure",
            "message":"uid provided is not a business account"
        }), 401
    bid = get_curr_bid()
    
    data = request.get_json()
    day = data['day'].lower()
    open = data['open']
    close = data['close']
    is_closed = False
    days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    if not day:
        print('day of the week should not be null')
        return jsonify({
            "status":"failure",
            "message":"day of the week required"
        }), 400
    if day not in days:
        print("day not allowed")
        return jsonify({
            "status":"success",
            "message": f"{day} not an allowed type for day"
        }), 400
    if open is None and close is None:
        is_closed = True
    elif not open or not close:
        print("Both open and close or neither required")
        return jsonify({
            "status":"failure",
            "message":"Both open and close time must be provided or neither"
        }), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        insert_hours_of_operation = """
            insert into hours_of_operation (bid, day, open_time, close_time, is_closed)
            values (%s, %s, %s, %s, %s);
        """
        param = [bid, day, open, close, is_closed]
        cursor.execute(insert_hours_of_operation, param)
        id = cursor.lastrowid
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"inserted hours of operation",
            "row id":id
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

@operation.route('/delete', methods=['DELETE'])
def delete_slot():
    data = request.get_json()
    id = data['id'] if data['id'] else None
    if not id:
        print("Missing id")
        return jsonify({
            "status":"failure",
            "message":"missing id"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        delete_time_slot = """
            delete from hours_of_operation
            where id=%s;
        """
        cursor.execute(delete_time_slot, [id])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"time slot deleted"
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


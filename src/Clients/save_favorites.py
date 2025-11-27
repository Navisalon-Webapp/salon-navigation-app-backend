from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *

saved_favorites = Blueprint("saved_favorites", __name__, url_prefix='/saved')

@saved_favorites.route('/business', methods=['GET'])
@login_required
def get_saved_businesses():
    if(check_role() != 'customer'):
        print('Unauthorized User')
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 400
    cid = get_curr_cid()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query_saved_businesses = """
            select b.bid, b.name
            from saved_business sb
            join business b on sb.bid=b.bid
            where cid=%s;
        """
        cursor.execute(query_saved_businesses, [cid])
        results = cursor.fetchall()
        return jsonify({
            "status":"success",
            "message":"retrieved saved businesses",
            "businesses": results
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

@saved_favorites.route('/employee', methods=['GET'])
@login_required
def get_saved_employees():
    if(check_role() != 'customer'):
        print('Unauthorized User')
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 400
    cid = get_curr_cid()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query_saved_businesses = """
            select e.eid, u.first_name, u.last_name, b.bid, e.approved
            from saved_employee se
            join employee e on se.eid=e.eid,
            join users u on e.uid=u.uid,
            left join business b on e.bid=b.bid
            where cid=%s;
        """
        cursor.execute(query_saved_businesses, [cid])
        results = cursor.fetchall()
        return jsonify({
            "status":"success",
            "message":"retrieved saved employees",
            "employees": results
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

@saved_favorites.route('/business/add', methods=['POST'])
@login_required
def add_saved_business():
    if(check_role() != 'customer'):
        print('Unauthorized User')
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 400
    cid = get_curr_cid()

    data = request.get_json()
    bid = data['bid'] if data['bid'] else None

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_saved_business = """
            insert into saved_business(cid, bid)
            values (%s, %s);
        """
        cursor.execute(insert_saved_business, [cid, bid])
        return jsonify({
            "status":"success",
            "message":"added new saved business",
            "customer id": cid,
            "business id": bid
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
    
@saved_favorites.route('/employee/add', methods=['POST'])
@login_required
def add_saved_employee():
    if(check_role() != 'customer'):
        print('Unauthorized User')
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 400
    cid = get_curr_cid()

    data = request.get_json()
    eid = data['eid'] if data['eid'] else None

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_saved_employee = """
            insert into saved_employee(cid, eid)
            values (%s, %s);
        """
        cursor.execute(insert_saved_employee, [cid, eid])
        return jsonify({
            "status":"success",
            "message":"added new saved employee",
            "customer id": cid,
            "employee id": eid
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

@saved_favorites.route('/business/remove', methods=['DELETE'])
@login_required
def remove_saved_busines():
    if(check_role() != 'customer'):
        print('Unauthorized User')
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 400
    cid = get_curr_cid()

    data = request.get_json()
    bid = data['bid'] if data['bid'] else None

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        delete_saved_business = """
            delete from saved_business
            where cid=%s and bid=%s;
        """
        cursor.execute(delete_saved_business, [cid, bid])
        return jsonify({
            "status":"success",
            "message":"removed saved business",
            "customer id": cid,
            "business id": bid
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

@saved_favorites.route('/employee/remove', methods=['DELETE'])
@login_required
def remove_saved_employee():
    if(check_role() != 'customer'):
        print('Unauthorized User')
        return jsonify({
            "status":"failure",
            "message":"User is not a customer"
        }), 400
    cid = get_curr_cid()

    data = request.get_json()
    eid = data['eid'] if data['eid'] else None

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        delete_saved_employee = """
            delete from saved_employee
            where cid=%s and eid=%s;
        """
        cursor.execute(delete_saved_employee, [cid, eid])
        return jsonify({
            "status":"success",
            "message":"removed saved employee",
            "customer id": cid,
            "employee id": eid
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
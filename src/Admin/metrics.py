from flask import Blueprint, request, jsonify
from .admin_func import *
from .queries import *
from helper.utils import *
from flask_login import current_user, login_required
from mysql.connector import Error
from datetime import datetime

metrics = Blueprint("metrics",__name__,url_prefix='/admin')

@metrics.route('/retention', methods=['GET'])
@login_required
def get_retention_metrics():
    """Return list of int

    size = max(appointments made by single customer at business) + 1

    for i in list

        i is number of appointments made by single customer at a business
        
        list[i] is number of customers that made i appointments at a business
    """
    if not check_role(current_user.id) == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    data = request.get_json()
    bid = data['bid']

    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_business_retention,[bid])
        retention = cursor.fetchall()
        max = retention[len(retention)-1]['x']
        retention_list = [0] * (max+1)
        for x in retention:
            retention_list[x['x']] = x['y']

        return jsonify(retention_list)
        
            
    except mysql.connector.Error as e:
        return jsonify({"status": "failure", "message": f"db error: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "failure", "message": f"error: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            cursor.close()
    
@metrics.route('/retention-rate', methods=['GET'])
@login_required
def retention_rate():
    if not check_role(current_user.id) == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    data = request.get_json()
    bid:int = data['bid'] if data['bid'] else None
    month:int = data['month'] if data['month'] else None
    year:int = data['year'] if data['month'] else None
    if not bid or not month or not year:
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        })
    
    param = [bid, month, year]
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query_new_customers,param)
        result = cursor.fetchone()
        countNew = result[0]
        cursor.execute(query_old_customers,param)
        result = cursor.fetchone()
        countOld = result[0]
        cursor.execute(query_all_customers,param)
        result = cursor.fetchone()
        countAll = result[0]
        retention_rate = (countAll-countNew)/countOld
        return jsonify({
            "status":"success",
            "message":"retrieved customer metrics",
            "old customers":countOld,
            "new customers":countNew,
            "total customers":countAll,
            "retention-rate":retention_rate
        })
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        })
    except Exception as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        })
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/customer-satisfaction', methods=['GET'])
def customer_satisfaction():
    data = request.get_json()
    bid:int = data['bid'] if data['bid'] else None
    if not bid:
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        })

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query_customer_satisfaction,[bid])
        result = cursor.fetchone()
        return jsonify({
            "status":"success",
            "message":"retrieved business average rating",
            "customer satisfaction": result[0]
        })
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        })
    except Exception as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        })
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
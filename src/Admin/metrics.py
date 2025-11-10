from flask import Blueprint, request, jsonify
from .admin_func import *
from .queries import *
from helper.utils import *
from flask_login import current_user, login_required
from mysql.connector import Error

metrics = Blueprint("metrics",__name__,url_prefix='/admin')

@metrics.route('/retention',methods=['GET'])
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
    
    
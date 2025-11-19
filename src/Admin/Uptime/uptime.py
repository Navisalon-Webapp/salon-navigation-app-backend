from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from helper.utils import *
from mysql.connector import Error
from datetime import datetime

uptime = Blueprint('uptime',__name__, url_prefix='/uptime')


@uptime.route('/health', methods=['GET'])
def health_check():
    """health check"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'backend'
            }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500
    
@uptime.route('/downtime', methods=['GET'])
def get_downtime():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error":str(e)
        })
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error":str(e)
        })
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
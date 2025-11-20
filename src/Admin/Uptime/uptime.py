from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from helper.utils import *
from .queries import *
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
    
@uptime.route('/current', methods=['GET'])
def get_current_uptime():
    """Return start time, updated at, and uptime in seconds of current running session"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(current_session_uptime)
        results = cursor.fetchone()
        print(results)
        return jsonify({
            "status":"success",
            "message":"returned current service session information",
            "start time":results['start_time'].isoformat(),
            "last updated":results['updated_at'].isoformat(),
            "uptime in seconds":results['uptime_seconds']
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error":str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error":str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@uptime.route('/downtime', methods=['GET'])
def get_downtime():
    """Return downtime information in last 24 hours and how many times server went down"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(downtime_24_hours)
        results = cursor.fetchall()
        for d in results:
            d['outage_start'] = d['outage_start'].isoformat()
            d['recovery_time'] = d['recovery_time'].isoformat()
        return jsonify({
            "status":"success",
            "downtimes":results,
            "downtime count":len(results)
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error":str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error":str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
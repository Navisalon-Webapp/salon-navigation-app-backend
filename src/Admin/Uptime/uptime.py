from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from helper.utils import *
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
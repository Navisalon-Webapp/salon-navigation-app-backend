from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from src.Admin.service_manager import service_manager
from src.Admin.health_moniter import health_monitor
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
                'service': 'backend',
                'service_id': service_manager.service_id,
                'uptime_since': service_manager.start_time.isoformat()
            }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500
    
@uptime.route('/health/status', methods=['GET'])
def health_status():
    """Get current health status and service information"""
    try:
        with service_manager.get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM service_time 
                WHERE id = %s
            """, (service_manager.service_id,))
            service_record = cursor.fetchone()
        
        return jsonify({
            'service_record': service_record,
            'current_time': datetime.now().isoformat(),
            'monitoring_status': 'active' if health_monitor.monitoring else 'inactive'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@uptime.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start health monitoring"""
    health_monitor.start_monitoring()
    return jsonify({'status': 'monitoring started'})

@uptime.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop health monitoring"""
    health_monitor.stop_monitoring()
    return jsonify({'status': 'monitoring stopped'})

def on_shutdown():
    """Handle application shutdown"""
    print("Shutting down...")
    health_monitor.stop_monitoring()
        
        

    

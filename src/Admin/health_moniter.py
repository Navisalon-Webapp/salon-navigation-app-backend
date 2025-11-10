# health_monitor.py
import requests
import time
import threading
from datetime import datetime
from src.Admin.service_manager import service_manager

class HealthMonitor:
    def __init__(self, app_url="http://localhost:5000", check_interval=600):  # 10 minutes
        self.app_url = app_url
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread = None
    
    def check_health(self):
        """Perform health check and return status"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.app_url}/uptime/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy',
                    'response_time_ms': response_time,
                    'timestamp': datetime.now(),
                    'details': data
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time_ms': response_time,
                    'timestamp': datetime.now(),
                    'error': f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': 0,
                'timestamp': datetime.now(),
                'error': str(e)
            }
    
    def perform_health_check(self):
        """Perform health check and update database"""
        print(f"Performing health check at {datetime.now()}")
        
        health_result = self.check_health()
        is_healthy = health_result['status'] == 'healthy'
        
        # Update service time in database
        service_manager.update_uptime(is_healthy)
        
        # Log the result
        if is_healthy:
            print(f"Health check PASSED - Response time: {health_result['response_time_ms']:.2f}ms")
        else:
            print(f"Health check FAILED - Error: {health_result.get('error', 'Unknown error')}")
        
        return health_result
    
    def start_monitoring(self):
        """Start the periodic health monitoring"""
        if self.monitoring:
            print("Monitoring is already running")
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                self.perform_health_check()
                time.sleep(self.check_interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"Health monitoring started with {self.check_interval}s interval")
    
    def stop_monitoring(self):
        """Stop the health monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Health monitoring stopped")

# Global health monitor instance
health_monitor = HealthMonitor()
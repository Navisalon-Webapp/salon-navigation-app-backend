from mysql.connector import Error
from helper.utils import get_db_connection
from datetime import datetime
import requests

class Service():
    def __init__(self, app_url="http://localhost:5000"):
        self.id = None
        self.scheduler = None
        self.running = None
        self.app_url=app_url
        self.job_added = False
    
    def start(self):
        from src.extensions import scheduler
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("insert into service_time values ();")
            conn.commit()
            self.id = cursor.lastrowid
            self.running = True
        except Error as e:
            print(f"error {e}")
            return
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        self.start_monitoring(scheduler)


    def update_uptime(self,health_status=True):

        if not self.id:
            print("No service id available")
            return
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('update service_time set updated_at = now() where id = %s',[self.id])
            conn.commit()
            if health_status:
                self.running = True
            else:
                self.running = False    
        except Error as e:
            print(f"Update Error {e}")
            self.running = False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
    def health_check(self):
        print(f"Health check at {datetime.now()}")
        
        try:
            response = requests.get(f"{self.app_url}/uptime/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.update_uptime()
                return {
                    'status': 'healthy',
                    'timestamp': datetime.now(),
                    'details': data
                }
            else:
                print(f"Health check failed: {e}")
                self.update_uptime(health_status=False)
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            print(f"Health check error: {e}")
            self.update_uptime(health_status=False)
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def start_monitoring(self, scheduler, interval_minutes=5, interval_seconds=0):

        if self.job_added:
            print("Monitoring job already added")
            return

        self.scheduler = scheduler

        try:
            try:
                self.scheduler.remove_job(f"{self.id}")
                print(f"Removed existing job: {self.id}")
            except:
                pass

            self.scheduler.add_job(
                func=self.health_check,
                trigger='interval',
                minutes=interval_minutes,
                seconds=interval_seconds,
                id=f"{self.id}",
                replace_existing=True
            )

            self.job_added = True
            print(f"Health monitoring started for service {self.id} every {interval_minutes} minutes {interval_seconds} seconds")
        except Exception as e:
            print(f"failed to start monitoring {e}")
            

    def stop_monitoring(self):

        if not self.job_added:
            print("No job to stop")
            return
        try:
            self.scheduler.remove_job(f"{self.id}")
            self.job_added = False
            self.running = False
        except Exception as e:
            print(f"Failed to stop monitoring: {e}")


    

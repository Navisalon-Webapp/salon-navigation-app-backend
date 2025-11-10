# service_manager.py
from flask import Flask
import mysql.connector
from datetime import datetime, timedelta
# import time
# import threading
# import requests
from contextlib import contextmanager

class ServiceTimeManager:
    def __init__(self, app=None):
        self.app = app
        self.service_id = None
        self.start_time = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self._initialize_service_record()
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = mysql.connector.connect(
            host='localhost',
            user='your_username',
            password='your_password',
            database='your_database'
        )
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_service_record(self):
        """Insert a new record when the app starts up"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert new service record
                cursor.execute("INSERT INTO service_time values();")
                
                # Get the generated ID
                self.service_id = cursor.lastrowid
                self.start_time = datetime.now()
                
                conn.commit()
                
                print(f"Service started with ID: {self.service_id} at {self.start_time}")
                
        except Exception as e:
            print(f"Error initializing service record: {e}")
            # Fallback: try to get the latest service record
            self._get_latest_service_record()
    
    def _get_latest_service_record(self):
        """Fallback to get the latest service record if initialization fails"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, start_time FROM service_time 
                    ORDER BY start_time DESC LIMIT 1
                """)
                result = cursor.fetchone()
                if result:
                    self.service_id, self.start_time = result
                    print(f"Using existing service record: {self.service_id}")
        except Exception as e:
            print(f"Error getting latest service record: {e}")
    
    def update_uptime(self, health_status=True):
        """Update the uptime based on health check results"""
        if not self.service_id:
            print("No service ID available")
            return False
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                if health_status:
                    # Calculate current uptime
                    current_time = datetime.now()
                    uptime_duration = current_time - self.start_time
                    
                    # Convert to time object (handle days)
                    total_seconds = int(uptime_duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # Update the record
                    cursor.execute("""
                        UPDATE service_time 
                        SET uptime = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (uptime_str, self.service_id))
                    
                    print(f"Uptime updated: {uptime_str}")
                    
                else:
                    # Service is down, you might want to handle this differently
                    cursor.execute("""
                        UPDATE service_time 
                        SET updated_at = NOW()
                        WHERE id = %s
                    """, (self.service_id,))
                    print("Health check failed - updated timestamp only")
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating uptime: {e}")
            return False

# Initialize the service manager
service_manager = ServiceTimeManager()
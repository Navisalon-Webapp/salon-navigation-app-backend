from flask import jsonify, Blueprint
from flask_login import login_required, current_user
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

revenue = Blueprint('revenue', __name__)


def get_db():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return db
    except mysql.connector.Error as err:
        print(f"Error: Database could not connect. : {err}")
        return None


def get_business_id():
    uid = getattr(current_user, 'id', None)
    if not uid:
        return None
    
    db = None
    cursor = None
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor(buffered=True)
        query = "SELECT bid FROM business WHERE uid = %s"
        cursor.execute(query, (uid,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"Error getting business ID: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@revenue.route("/api/owner/get-revenue", methods=["GET"])
@login_required
def get_revenue():
    bid = get_business_id()
    
    if not bid:
        return jsonify({"message": "Business not found for current user."}), 404
    
    db = None
    cursor = None
    
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor(buffered=True)
        
        # Get today's revenue
        daily_query = """
        SELECT COALESCE(SUM(s.price), 0) as daily_revenue
        FROM appointments a
        JOIN services s ON a.sid = s.sid
        JOIN employee e ON a.eid = e.eid
        WHERE e.bid = %s 
        AND DATE(a.start_time) = CURDATE()
        AND a.end_time IS NOT NULL
        """
        cursor.execute(daily_query, (bid,))
        daily_result = cursor.fetchone()
        daily_revenue = float(daily_result[0]) if daily_result else 0.0
        
        # Get this week's revenue
        weekly_query = """
        SELECT COALESCE(SUM(s.price), 0) as weekly_revenue
        FROM appointments a
        JOIN services s ON a.sid = s.sid
        JOIN employee e ON a.eid = e.eid
        WHERE e.bid = %s 
        AND YEARWEEK(a.start_time, 1) = YEARWEEK(CURDATE(), 1)
        AND a.end_time IS NOT NULL
        """
        cursor.execute(weekly_query, (bid,))
        weekly_result = cursor.fetchone()
        weekly_revenue = float(weekly_result[0]) if weekly_result else 0.0
        
        # Get this month's revenue
        monthly_query = """
        SELECT COALESCE(SUM(s.price), 0) as monthly_revenue
        FROM appointments a
        JOIN services s ON a.sid = s.sid
        JOIN employee e ON a.eid = e.eid
        WHERE e.bid = %s 
        AND MONTH(a.start_time) = MONTH(CURDATE())
        AND YEAR(a.start_time) = YEAR(CURDATE())
        AND a.end_time IS NOT NULL
        """
        cursor.execute(monthly_query, (bid,))
        monthly_result = cursor.fetchone()
        monthly_revenue = float(monthly_result[0]) if monthly_result else 0.0
        
        # Get this year's revenue
        yearly_query = """
        SELECT COALESCE(SUM(s.price), 0) as yearly_revenue
        FROM appointments a
        JOIN services s ON a.sid = s.sid
        JOIN employee e ON a.eid = e.eid
        WHERE e.bid = %s 
        AND YEAR(a.start_time) = YEAR(CURDATE())
        AND a.end_time IS NOT NULL
        """
        cursor.execute(yearly_query, (bid,))
        yearly_result = cursor.fetchone()
        yearly_revenue = float(yearly_result[0]) if yearly_result else 0.0
        
        return jsonify({
            "daily": daily_revenue,
            "weekly": weekly_revenue,
            "monthly": monthly_revenue,
            "yearly": yearly_revenue
        }), 200
        
    except mysql.connector.Error as err:
        print(f"Error fetching revenue: {err}")
        return jsonify({"message": "Failed to fetch revenue data."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

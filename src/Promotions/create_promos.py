from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from flask_login import current_user, login_required
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.extensions import scheduler
from src.Notifications.notification_func import *
import os
from .promo_func import *

load_dotenv()

promotions = Blueprint('promotions', __name__)

def get_db():

    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            port=int(os.getenv("DB_PORT")),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
            )
        return db
    except mysql.connector.Error as err:
        print(f"Error: Database could not connect. : {err}")
        return None

def send_promo(msg, email):
    from app import app
    from flask import current_app
    try:
        app_context = current_app._get_current_object()
    except RuntimeError:
        app_context = app
    with app_context.app_context():
        email_message(current_app._get_current_object(),msg,email)

#Owners can create promotions
@promotions.route("/api/owner/create-promotion", methods=["POST"])
@login_required
def create_promos():
    data = request.get_json()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    is_recurring = data.get("is_recurring", False)
    recurr_days = data.get("recurr_days", None)
    start_time = data.get("start_time", None)
    end_time = data.get("end_time", None)
    title = data.get("title", None)
    description = data.get("description", None)
    bid = get_curr_bid()
    threshold = data.get("threshold")
    prog_type = data.get("prog_type")
    reward_type = data.get("reward_type")
    reward_value = data.get("rwd_value")
    description = data.get("description")
    
    required_fields = {
        "start_date": start_date,
        "end_date": end_date,
        "reward_type": reward_type,
        "reward_value": reward_value
    } 

    missing_or_null_fields = [field for field, value in required_fields.items() if value is None]
    if missing_or_null_fields:
        return jsonify({"message": f"Missing required fields or null values: {', '.join(missing_or_null_fields)}."}), 400

    allowed_reward_types = ["is_appt","is_product","is_price", "is_points", "is_discount"]
    if reward_type not in allowed_reward_types:
        return jsonify({"message": "Invalid reward type. "
        "Must literally use the terms in quotes: 'is_appt','is_product','is_price', 'is_points', 'is_discount'. "}), 400

    if is_recurring and recurr_days is None:
        return jsonify({"message": "If promotion is recurring, it needs a recurrence day (example: Monday)."}), 400
    
    if isinstance(recurr_days, list):
        recurr_days = ",".join(recurr_days)
    
    db = None
    cursor = None

    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor(buffered=True)

        query_lprog = f"""
        insert into loyalty_programs(bid, {prog_type}, threshold, description)
        values(%s, %s, %s, %s);
        """
        cursor.execute(query_lprog, (bid, True, threshold, description))
        lprog_id = cursor.lastrowid

        query_rwd = f"""
        insert into rewards(bid, lprog_id, {reward_type}, rwd_value)
        values(%s,%s, %s, %s);
        """
        cursor.execute(query_rwd, (bid, lprog_id, True, reward_value))

        query = """ 
        insert into promotions(lprog_id, title, start_date, end_date, is_recurring, recurr_days, start_time, end_time, description)
        values(%s, %s, %s, %s, %s, %s, %s, %s, %s);
         """
        cursor.execute(query, (lprog_id, title, start_date, end_date, is_recurring, recurr_days, start_time, end_time, description))
        promo_id = cursor.lastrowid
        db.commit() 
        
        cursor.execute("select b.bid, b.name from business b join users u on b.uid=u.uid where u.uid=%s",[current_user.id])
        row = cursor.fetchone()
        msg = create_promo_message(title, description, row[1])
        customers = get_business_customers(row[0])
        send_to = []
        for c in customers:
            if check_promotion_subscription(c['cid']):
                send_to.append(c['email'])
        scheduler.add_job(
            func=lambda:send_promo(msg,send_to),
            trigger='date',
            run_date=datetime.now()+timedelta(seconds=30),
            id=f"Promotion:{promo_id}:{row[0]}"
        )

        return jsonify({"message": "Promotion created successfully.", "promotion_id":promo_id}), 201
    except mysql.connector.Error as err:
        print(f"Error: Promotion creation unsuccessful. : {err}")
        if db:
            db.rollback() 
        return jsonify({"message": "Failed to create promotion."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()



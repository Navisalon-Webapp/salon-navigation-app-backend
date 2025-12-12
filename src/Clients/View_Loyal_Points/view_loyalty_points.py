from flask import jsonify, Blueprint
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import current_user, login_required
from typing import Optional


load_dotenv()

view_lpoints = Blueprint('view_lpoints', __name__)





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

#get current logged-in client's customer id
def get_cid():
    uid = getattr(current_user, 'id', None)
    if uid is None:
        print("Error: No UID found in request context.")
        return None
    
    db = get_db()
    if db is None:
        print("Error: Could not establish connection to the database.")
        return None
    cursor = db.cursor(buffered=True)
    try:
        query = "select cid from customers where uid = %s;"
        cursor.execute(query, (uid,))
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
            return customer_id
        else:
            print("Error: No customer found for the given UID.")
            return None
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return None
    finally:
        cursor.close()
        db.close()
    
    


#Clients can view their Loyalty Points Balance
@view_lpoints.route("/api/clients/view-loyalty-points", methods=["GET"])
@login_required #can only be accessed by logged in users
def view_loyalty_points():
    
    
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
        
        customer_id = get_cid()
        if customer_id is None:
            return jsonify({"message": "Could not retrieve customer ID."}), 500
        
        cursor = db.cursor(dictionary=True, buffered=True)
        query = """
            select b.bid,
                   b.name,
                   clp.pts_balance as points_balance,
                   lp.lprog_id,
                   lp.threshold,
                   lp.appts_thresh,
                   lp.pdct_thresh,
                   lp.points_thresh,
                   lp.price_thresh,
                   r.is_appt,
                   r.is_product,
                   r.is_price,
                   r.is_points,
                   r.is_discount,
                   r.rwd_value,
                   clp.appt_complete,
                   clp.prod_purchased,
                   clp.amount_spent
            from customer_loyalty_points clp
            join business b on clp.bid = b.bid
            left join loyalty_programs lp on lp.bid = clp.bid
            left join rewards r on r.lprog_id = lp.lprog_id and r.bid = clp.bid
            where clp.cid = %s
            order by b.name, lp.lprog_id desc;
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        loyalty_points = []
        seen_bids = set()
        reward_flags = [
            ("is_appt", "Free Appointment"),
            ("is_product", "Free Product"),
            ("is_price", "Price Credit"),
            ("is_points", "Bonus Points"),
            ("is_discount", "Discount"),
        ]
        for row in results:
            bid = row.get("bid")
            name = row.get("name")
            if bid is None:
                continue
            if bid in seen_bids:
                continue
            seen_bids.add(bid)
            points_balance = float(row.get("points_balance") or 0)
            threshold = row.get("threshold")
            program_type = next(
                (
                    flag
                    for flag, active in (
                        ("appts_thresh", row.get("appts_thresh")),
                        ("pdct_thresh", row.get("pdct_thresh")),
                        ("points_thresh", row.get("points_thresh")),
                        ("price_thresh", row.get("price_thresh")),
                    )
                    if active
                ),
                None,
            )
            active_reward = next((label for key, label in reward_flags if row.get(key)), None)
            reward_value = row.get("rwd_value")

            progress_value = points_balance
            goal_value: Optional[float]
            try:
                goal_value = float(threshold) if threshold is not None else None
            except (TypeError, ValueError):
                goal_value = None

            if program_type == "appts_thresh":
                progress_value = float(row.get("appt_complete") or 0)
            elif program_type == "pdct_thresh":
                progress_value = float(row.get("prod_purchased") or 0)
            elif program_type == "price_thresh":
                progress_value = float(row.get("amount_spent") or 0)
            elif program_type == "points_thresh":
                progress_value = points_balance

            if goal_value is None:
                if program_type == "points_thresh":
                    goal_value = max(progress_value, 100.0)
                else:
                    goal_value = 1.0

            progress_value = max(progress_value, 0.0)
            goal_value = max(goal_value, 0.0)
            if goal_value and goal_value > 0:
                progress_value = min(progress_value, goal_value)

            rounded_points = int(round(points_balance))
            rounded_progress = int(round(progress_value))
            rounded_goal = int(round(goal_value))

            loyalty_points.append(
                {
                    "id": f"s{bid}",
                    "bid": bid,
                    "name": name,
                    "points": rounded_points,
                    "progress": rounded_progress,
                    "goal": rounded_goal,
                    "programType": program_type,
                    "rewardType": active_reward,
                    "rewardValue": int(round(float(reward_value))) if reward_value is not None else None,
                    "address": "",
                }
            )
        return jsonify(loyalty_points), 200
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return jsonify({"message": "Database query failed."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()





from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

loyalty_prog = Blueprint('loyalty_prog', __name__)





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




#Salon Owner can create loyalty programs
@loyalty_prog.route("/api/owner/create-loyalty-programs", methods=["POST"])
def create_lprogs():
    data = request.get_json()

    business_id = data.get("bid")
    threshold = data.get("threshold")
    prog_type = data.get("prog_type")
    reward_type = data.get("reward_type")
    reward_value = data.get("rwd_value")

    allowed_prog_types = ["appts_thresh", "pdct_thresh","points_thresh", "price_thresh"]
    if prog_type not in allowed_prog_types:
        return jsonify({"message": "Invalid program type. Must literally use the terms in quotes: 'appts_thresh', 'pdct_thresh','points_thresh', 'price_thresh'. "}), 400
    
    allowed_reward_types = ["is_appt","is_product","is_price", "is_points", "is_discount"]
    if reward_type not in allowed_reward_types:
        return jsonify({"message": "Invalid reward type. "
        "Must literally use the terms in quotes: 'is_appt','is_product','is_price', 'is_points', 'is_discount'. "}), 400
    
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor(buffered=True)

        #f string: cleanly insert prog_type into query
        query_lprog = f"""
        insert into loyalty_programs(bid, {prog_type}, threshold)
        values(%s, %s, %s);
         """
        cursor.execute(query_lprog, (business_id, True, threshold))
        lprog_id = cursor.lastrowid
        query_rwd = f"""
        insert into rewards(bid, lprog_id, {reward_type}, rwd_value)
        values(%s,%s, %s, %s);
         """
        cursor.execute(query_rwd, (business_id, lprog_id, True, reward_value))
        db.commit()
        return jsonify({"message": "Loyalty program created successfully.", "lprog_id": lprog_id }), 201
    except mysql.connector.Error as err:
        print(f"Error: Loyalty program creation unsuccessful. : {err}")
        if db:
            db.rollback() 
        return jsonify({"message": "Failed to create loyalty program."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()







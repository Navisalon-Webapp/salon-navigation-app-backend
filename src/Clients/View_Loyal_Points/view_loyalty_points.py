from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import current_user, login_required


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
        
        cursor = db.cursor(buffered=True)

        
        query = """
        select b.bid, b.name, clp.pts_balance as points_balance
        from customer_loyalty_points clp join business b on clp.bid = b.bid
        where clp.cid = %s;
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        loyalty_points = []
        for (bid, name, points_balance) in results:
            loyalty_points.append({
                "id": f"s{bid}",
                "bid": bid,
                "name": name,
                "points": float(points_balance) if points_balance else 0,
                "goal": 100,
                "address": ""
            })
        return jsonify(loyalty_points), 200
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return jsonify({"message": "Database query failed."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()





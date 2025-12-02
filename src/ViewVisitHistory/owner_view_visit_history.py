from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import login_required, current_user


load_dotenv()

visit_hist = Blueprint('visit_hist', __name__)





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

#get current logged-in owner's business id
def get_current_owner_bid():
    uid = getattr(current_user, 'id', None)
    if uid is None:
        print("Error: No UID found in request context.")
        return None
    
    db = get_db()
    if db is None:
        print("Error: Could not establish connection to the database.")
        return None
    cursor = db.cursor()
    try:
        query = "select bid from business where uid = %s;"
        cursor.execute(query, (uid,))
        result = cursor.fetchone()
        if result:
            business_id = result[0]
            return business_id
        else:
            print("Error: No business found for the given UID.")
            return None
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return None
    finally:
        cursor.close()
        db.close()
    
    



#Salon Owner can view client visit history
@visit_hist.route("/api/owner/view-visit-history", methods=["GET"])
@login_required #can only be accessed by logged in users
def view_hist():
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
        
        bid = get_current_owner_bid()

        if bid is None:
            return jsonify({"message": "Could not determine business ID for the owner."}), 400
        cursor = db.cursor()

        
        query = """
        SELECT c.cid as customer_id, CONCAT(u.first_name, ' ', u.last_name) as customer_name, e.eid as employee_id, CONCAT(eu.first_name,' ', eu.last_name) as employee_name, s.name, s.price, a.start_time, a.expected_end_time, a.end_time, a.notes
        FROM users u JOIN customers c ON u.uid = c.uid
        JOIN appointments a on c.cid = a.cid
        LEFT JOIN employee e ON a.eid = e.eid
        LEFT JOIN users eu ON e.uid = eu.uid
        JOIN services s ON a.sid = s.sid
        JOIN business b ON e.bid = b.bid
        WHERE b.bid = %s
        ORDER BY a.start_time DESC;
        """
        cursor.execute(query, (bid,))
        rows = cursor.fetchall()
        history = [{"customer_id": row[0], "customer_name": row[1],
                    "employee_id": row[2], "employee_name": row[3],
                    "service_name": row[4], "service_price": float(row[5]),
                    "start_time": row[6].isoformat() if row[6] else None,
                    "expected_end_time": row[7].isoformat() if row[7] else None,
                    "end_time": row[8].isoformat() if row[8] else None,
                    "notes": row[9]} for row in rows]
        return jsonify(history)
    except mysql.connector.Error as err:
        print(f"Error: Could not retrieve visit history. : {err}")
        return jsonify({"message": "Failed to retrieve visit history."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
        






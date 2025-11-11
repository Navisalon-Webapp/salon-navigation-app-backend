from flask import jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import current_user, login_required


load_dotenv()


client_browse = Blueprint('clients_browse', __name__)


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
    cursor = db.cursor()
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


#clients can browse salons
@client_browse.route("/api/client/browse-salons", methods=["GET"])
@login_required
def browse_salons():
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor()
        
        query = """ 
        SELECT b.bid, b.name, a.street, 
        a.city, a.state, a.country, a.zip_code
        FROM business b JOIN addresses a ON b.aid = a.aid
        WHERE b.status = true;
         """
        cursor.execute(query)
        rows = cursor.fetchall()
        salons = [{"business_id": row[0], "business_name": row[1],
                     "street": row[2], "city": row[3],
                     "state": row[4], "country": row[5],
                     "zip_code": row[6]} for row in rows]
        return jsonify(salons)
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return jsonify({"message": "Database query failed."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


#clients can browse workers
@client_browse.route("/api/client/browse-workers", methods=["GET"])
@login_required
def browse_workers():
    
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
        
        cursor = db.cursor()
        
        query = """ 
select e.eid, u.first_name, u.last_name, GROUP_CONCAT(ex.expertise SEPARATOR ', ') AS expertises,
       b.name AS business_name, b.bid AS business_id, 
       a.street, a.city, a.state, a.country, a.zip_code
FROM employee e 
JOIN employee_expertise ee ON e.eid = ee.eid
JOIN expertise ex ON ee.exp_id = ex.exp_id 
JOIN users u ON e.uid = u.uid
JOIN business b ON e.bid = b.bid
JOIN addresses a ON b.aid = a.aid
WHERE e.approved = true
GROUP BY e.eid, u.first_name, u.last_name, b.name, b.bid, a.street, a.city, a.state, a.country, a.zip_code;
 """
        cursor.execute(query)
        rows = cursor.fetchall()
        workers = [{"employee_id": row[0], "first_name": row[1], 
                   "last_name": row[2], "expertises": row[3],
                   "business_name": row[4], "business_id": row[5],
                   "street": row[6], "city": row[7], "state": row[8],
                   "country": row[9], "zip_code": row[10]} for row in rows]
        return jsonify(workers)
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return jsonify({"message": "Database query failed."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
            
        



#clients can browse previous appointments
@client_browse.route("/api/clients/view-prev-appointments", methods=["GET"])
@login_required #can only be accessed by logged in clients
def client_view_appoints():
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
        
        cursor = db.cursor()
        
        query = """ 
        select a.aid as appointment_id, s.name as service_name, s.price as service_price, u.first_name, 
        u.last_name, e.eid as employee_id, a.start_time, a.expected_end_time, a.end_time
        from appointments a
        join employee e on a.eid = e.eid
        join services s on a.sid = s.sid
        join users u on e.uid = u.uid
        join customers c on a.cid = c.cid
        where a.cid = %s; 
        """

        cursor.execute(query, (customer_id,))
        rows = cursor.fetchall()
        appointments = [{"appointment_id": row[0], "service_name": row[1], 
                   "service_price": row[2], "employee_first_name": row[3],
                   "employee_last_name": row[4], "employee_id": row[5],
                   "start_time": row[6], "expected_end_time": row[7],
                   "end_time": row[8]} for row in rows]
        return jsonify(appointments)
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return jsonify({"message": "Database query failed."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
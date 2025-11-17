from flask import jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
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



#clients can browse salons
@client_browse.route("/api/client/browse-salons", methods=["GET"])
@login_required
def browse_salons():
    query = """ 
        SELECT b.bid, b.name, a.street, 
        a.city, a.state, a.country, a.zip_code
        FROM business b JOIN addresses a ON b.aid = a.aid
    """
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        salons = [{"business_id": row[0], "name": row[1], 
                "street": row[2], "city": row[3], "state": row[4], 
                    "country": row[5], "zip_code": row[6]} for row in rows]
        return jsonify(salons)
    except Error as e:
        return jsonify({
            "status":"failure",
            "message":f"Database Error {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "status":"failure",
            "message":f"Error {str(e)}"
        })
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


#clients can browse workers
@client_browse.route("/api/client/browse-workers", methods=["GET"])
@login_required
def browse_workers():
    query = """ 
        SELECT e.eid,u.first_name, u.last_name, ex.expertise,
        b.name AS business_name, b.bid AS business_id, 
        a.street, a.city, a.state, a.country, a.zip_code
        FROM employee e JOIN employee_expertise ee ON e.eid = ee.eid
        JOIN expertise ex ON ee.exp_id = ex.exp_id 
        JOIN users u ON e.uid = u.uid
        JOIN business b ON e.bid = b.bid
        JOIN addresses a ON b.aid = a.aid
    """
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"[browse_workers] Query returned {len(rows)} rows")
        workers = [{"employee_id": row[0], "employee_first_name": row[1], 
                    "employee_last_name": row[2], "expertise": row[3],
                    "business_name": row[4], "business_id": row[5],
                    "street": row[6], "city": row[7], "state": row[8],
                    "country": row[9], "zip_code": row[10]
                    } for row in rows]
        print(f"[browse_workers] Returning {len(workers)} workers")
        return jsonify(workers)
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": f"Database Error {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": f"Error {str(e)}"
        })
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()





#clients can browse previous appointments
@client_browse.route("/api/clients/view-prev-appointments", methods=["GET"])
@login_required #can only be accessed by logged in clients
def client_view_appoints():
    # First get the customer ID for the current user
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        cid_query = "SELECT cid FROM customers WHERE uid = %s"
        cursor.execute(cid_query, (current_user.id,))
        cid_result = cursor.fetchone()
        
        if not cid_result:
            return jsonify({"error": "Customer not found"}), 404
        
        cid = cid_result[0]
        
        query = """ 
            select a.aid as appointment_id, s.name as service_name, s.price as service_price, u.first_name, 
            u.last_name, e.eid as employee_id, a.start_time, a.expected_end_time, a.end_time
            from appointments a
            join employee e on a.eid = e.eid
            join services s on a.sid = s.sid
            join users u on e.uid = u.uid
            WHERE a.cid = %s AND a.start_time < NOW()
            ORDER BY a.start_time DESC
        """

        cursor.execute(query, (cid,))
        rows = cursor.fetchall()
        appointments = [{"appointment_id": row[0], "service_name": row[1], 
                    "service_price": row[2], "employee_first_name": row[3],
                    "employee_last_name": row[4], "employee_id": row[5],
                    "start_time": row[6], "expected_end_time": row[7],
                    "end_time": row[8]
                    } for row in rows]
        return jsonify(appointments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            db.close()
        if db:
            db.close()


#clients can browse future appointments
@client_browse.route("/api/clients/view-future-appointments", methods=["GET"])
@login_required #can only be accessed by logged in clients
def client_view_future_appoints():
    # First get the customer ID for the current user
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        cid_query = "SELECT cid FROM customers WHERE uid = %s"
        cursor.execute(cid_query, (current_user.id,))
        cid_result = cursor.fetchone()
        
        if not cid_result:
            return jsonify({"error": "Customer not found"}), 404
        
        cid = cid_result[0]
        
        query = """ 
            select a.aid as appointment_id, s.name as service_name, s.price as service_price, u.first_name, 
            u.last_name, e.eid as employee_id, a.start_time, a.expected_end_time, a.end_time
            from appointments a
            join employee e on a.eid = e.eid
            join services s on a.sid = s.sid
            join users u on e.uid = u.uid
            WHERE a.cid = %s AND a.start_time >= NOW()
            ORDER BY a.start_time ASC
        """

        cursor.execute(query, (cid,))
        rows = cursor.fetchall()
        appointments = [{"appointment_id": row[0], "service_name": row[1], 
                    "service_price": row[2], "employee_first_name": row[3],
                    "employee_last_name": row[4], "employee_id": row[5],
                    "start_time": row[6], "expected_end_time": row[7],
                    "end_time": row[8]
                    } for row in rows]
        return jsonify(appointments)
    except Exception as e:
        print(f"[ERROR] Future appointments error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

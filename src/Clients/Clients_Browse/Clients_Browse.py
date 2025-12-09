from flask import jsonify, Blueprint, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from flask_login import current_user, login_required
from datetime import datetime

from src.LoyaltyProgram.loyalty_service import award_points_for_visit

load_dotenv()

client_browse = Blueprint('clients_browse', __name__)

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

#clients can browse salons
@client_browse.route("/api/client/browse-salons", methods=["GET"])
@login_required
def browse_salons():
    query = """ 
        SELECT b.bid, b.name, a.street,
        a.city, a.state, a.country, a.zip_code,
        GROUP_CONCAT(DISTINCT s.name ORDER BY s.name SEPARATOR ', ') AS services
        FROM business b
        JOIN addresses a ON b.aid = a.aid
        LEFT JOIN services s ON b.bid = s.bid
        GROUP BY b.bid
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
                    "country": row[5], "zip_code": row[6], "services": row[7]} for row in rows]
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
        SELECT e.eid, u.first_name, u.last_name,
        GROUP_CONCAT(DISTINCT s.name ORDER BY s.name SEPARATOR ', ') AS services,
        GROUP_CONCAT(DISTINCT sc.name ORDER BY sc.name SEPARATOR ', ') AS categories,
        b.name AS business_name, b.bid AS business_id,
        a.street, a.city, a.state, a.country, a.zip_code
        FROM employee e
        JOIN employee_services es ON e.eid = es.eid
        JOIN services s ON es.sid = s.sid
        JOIN service_categories sc ON s.cat_id = sc.cat_id
        JOIN users u ON e.uid = u.uid
        JOIN business b ON e.bid = b.bid
        JOIN addresses a ON b.aid = a.aid
        WHERE e.approved = true
        GROUP BY e.eid
    """
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        workers = [{"employee_id": row[0], "employee_first_name": row[1], 
                    "employee_last_name": row[2], "services": row[3], "categories": row[4],
                    "business_name": row[5], "business_id": row[6],
                    "street": row[7], "city": row[8], "state": row[9],
                    "country": row[10], "zip_code": row[11]
                    } for row in rows]
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


@client_browse.route("/api/client/business-workers/<int:business_id>", methods=["GET"])
@login_required
def get_business_workers(business_id: int):
    query = """
        SELECT e.eid,
               u.first_name,
               u.last_name,
               GROUP_CONCAT(DISTINCT ex.expertise ORDER BY ex.expertise SEPARATOR ', ') AS expertise,
               e.bio,
               e.profile_picture,
               e.approved
        FROM employee e
        JOIN users u ON e.uid = u.uid
        LEFT JOIN employee_expertise ee ON e.eid = ee.eid
        LEFT JOIN expertise ex ON ee.exp_id = ex.exp_id
        WHERE e.bid = %s
        GROUP BY e.eid, u.first_name, u.last_name, e.bio, e.profile_picture, e.approved
        ORDER BY u.first_name, u.last_name
    """

    db = None
    cursor = None
    try:
        db = get_db()
        if db is None:
            return jsonify({
                "status": "failure",
                "message": "Database connection failed"
            }), 500

        cursor = db.cursor(dictionary=True)
        cursor.execute(query, (business_id,))
        rows = cursor.fetchall()

        workers = []
        for row in rows:
            picture = row.get("profile_picture")
            if picture:
                if isinstance(picture, bytes):
                    picture = picture.decode("utf-8")
                if not str(picture).startswith("data:image"):
                    row["profile_picture"] = f"data:image/jpeg;base64,{picture}"
                else:
                    row["profile_picture"] = picture
            else:
                row["profile_picture"] = None

            workers.append({
                "employee_id": row["eid"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "expertise": row.get("expertise"),
                "bio": row.get("bio"),
                "profile_picture": row.get("profile_picture"),
                "approved": bool(row.get("approved")),
            })

        return jsonify(workers), 200
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": f"Database Error {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": f"Error {str(e)}"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@client_browse.route("/api/client/service-categories", methods=["GET"])
@login_required
def get_service_categories():
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT cat_id, name FROM service_categories ORDER BY name")
        rows = cursor.fetchall()

        categories = [{"cat_id": r[0], "name": r[1]} for r in rows]
        return jsonify(categories)
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
        cursor = db.cursor(dictionary=True, buffered=True)
        cid_query = "SELECT cid FROM customers WHERE uid = %s"
        cursor.execute(cid_query, (current_user.id,))
        cid_result = cursor.fetchone()
        
        if not cid_result:
            return jsonify({"error": "Customer not found"}), 404
        
        cid = cid_result['cid']
        
        query = """ 
            SELECT a.aid as appointment_id, s.name as service_name, s.price as service_price, 
            s.bid as business_id, u.first_name, u.last_name, e.eid as employee_id, a.start_time, a.expected_end_time, 
            a.end_time, s.duration
            FROM appointments a
            JOIN employee e ON a.eid = e.eid
            JOIN services s ON a.sid = s.sid
            JOIN users u ON e.uid = u.uid
            WHERE a.cid = %s AND a.start_time < NOW()
            ORDER BY a.start_time DESC
        """

        cursor.execute(query, (cid,))
        rows = cursor.fetchall()

        for row in rows:
            business_id = row.get('business_id')
            if business_id is None:
                continue
            try:
                award_points_for_visit(
                    db,
                    aid=row.get('appointment_id'),
                    cid=cid,
                    bid=business_id,
                    amount=row.get('service_price'),
                )
            except mysql.connector.Error as err:
                print(f"[WARN] Failed to award loyalty points for appointment {row.get('appointment_id')}: {err}")
            except Exception as err:
                print(f"[WARN] Unexpected error awarding loyalty points: {err}")

        formatted_appointments = []
        for row in rows:
            start_time = row.get('start_time')
            if isinstance(start_time, datetime):
                time_str = start_time.strftime('%I:%M %p')
                date_str = start_time.strftime('%m/%d/%Y')
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = str(start_time)
                date_str = ""
                start_time_str = str(start_time)
            
            formatted_appointments.append({
                "appointment_id": row['appointment_id'],
                "service_name": row['service_name'],
                "service_price": float(row['service_price']) if row['service_price'] else 0.0,
                "employee_first_name": row['first_name'],
                "employee_last_name": row['last_name'],
                "employee_id": row['employee_id'],
                "start_time": start_time_str,  # String format instead of datetime object
                "time": time_str,
                "date": date_str,
                "expected_end_time": row['expected_end_time'].strftime('%Y-%m-%d %H:%M:%S') if row['expected_end_time'] else None,
                "end_time": row['end_time'].strftime('%Y-%m-%d %H:%M:%S') if row['end_time'] else None,
                "duration": row.get('duration', 60),
                "status": "completed"
            })
        
        return jsonify(formatted_appointments)
    except Exception as e:
        print(f"[ERROR] Past appointments error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
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
        cursor = db.cursor(dictionary=True, buffered=True)
        cid_query = "SELECT cid FROM customers WHERE uid = %s"
        cursor.execute(cid_query, (current_user.id,))
        cid_result = cursor.fetchone()
        
        if not cid_result:
            return jsonify({"error": "Customer not found"}), 404
        
        cid = cid_result['cid']
        
        query = """ 
            SELECT a.aid as appointment_id, s.name as service_name, s.price as service_price, 
            u.first_name, u.last_name, e.eid as employee_id, a.start_time, a.expected_end_time, 
            a.end_time, s.duration
            FROM appointments a
            JOIN employee e ON a.eid = e.eid
            JOIN services s ON a.sid = s.sid
            JOIN users u ON e.uid = u.uid
            WHERE a.cid = %s AND a.start_time >= NOW()
            ORDER BY a.start_time ASC
        """

        cursor.execute(query, (cid,))
        rows = cursor.fetchall()
        
        formatted_appointments = []
        for row in rows:
            start_time = row.get('start_time')
            if isinstance(start_time, datetime):
                time_str = start_time.strftime('%I:%M %p')
                date_str = start_time.strftime('%m/%d/%Y')
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = str(start_time)
                date_str = ""
                start_time_str = str(start_time)
            
            formatted_appointments.append({
                "appointment_id": row['appointment_id'],
                "service_name": row['service_name'],
                "service_price": float(row['service_price']) if row['service_price'] else 0.0,
                "employee_first_name": row['first_name'],
                "employee_last_name": row['last_name'],
                "employee_id": row['employee_id'],
                "start_time": start_time_str,  # String format instead of datetime object
                "time": time_str,
                "date": date_str,
                "expected_end_time": row['expected_end_time'].strftime('%Y-%m-%d %H:%M:%S') if row['expected_end_time'] else None,
                "end_time": row['end_time'].strftime('%Y-%m-%d %H:%M:%S') if row['end_time'] else None,
                "duration": row.get('duration', 60),
                "status": "scheduled"
            })
        
        return jsonify(formatted_appointments)
    except Exception as e:
        print(f"[ERROR] Future appointments error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@client_browse.route("/api/client/business-info/<int:business_id>", methods=["GET"])
@login_required
def get_business_info(business_id):
    db = None
    cursor = None
    
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor(dictionary=True, buffered=True)
        
        business_query = """
        SELECT b.name, a.street, a.city, a.state, 
               a.country, a.zip_code, u.phone
        FROM business b
        JOIN addresses a ON b.aid = a.aid
        JOIN users u ON b.uid = u.uid
        WHERE b.bid = %s
        """
        cursor.execute(business_query, (business_id,))
        business = cursor.fetchone()
        
        if not business:
            return jsonify({"message": "Business not found."}), 404
        
        email_query = """
        SELECT email
        FROM authenticate
        WHERE uid = (SELECT uid FROM business WHERE bid = %s)
        """
        cursor.execute(email_query, (business_id,))
        email_result = cursor.fetchone()
        
        if email_result:
            business['email'] = email_result['email']
        
        return jsonify(business), 200
        
    except mysql.connector.Error as err:
        print(f"Error fetching business info: {err}")
        return jsonify({"message": "Failed to fetch business info."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@client_browse.route("/api/visit-history/salon-views", methods=["POST"])
@login_required
def inc_salon_view():
    db = None
    cursor = None
    try:
        data = request.get_json()
        bid = data.get("bid")
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cid_query = "SELECT cid FROM customers WHERE uid = %s"
        cursor.execute(cid_query, (current_user.id,))
        cid_result = cursor.fetchone()
        
        if not cid_result:
            return jsonify({"error": "Customer not found"}), 404
        
        cid = cid_result['cid']
        
        cursor.execute("""
            INSERT INTO visit_history (cid, bid, salon_views)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE salon_views = salon_views + 1;
        """, (cid, bid))
        db.commit()
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@client_browse.route("/api/visit-history/product-views", methods=["POST"])
@login_required
def inc_product_view():
    db = None
    cursor = None
    try:
        data = request.get_json()
        bid = data.get("bid")
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cid_query = "SELECT cid FROM customers WHERE uid = %s"
        cursor.execute(cid_query, (current_user.id,))
        cid_result = cursor.fetchone()
        
        if not cid_result:
            return jsonify({"error": "Customer not found"}), 404
        
        cid = cid_result['cid']
        
        cursor.execute("""
            INSERT INTO visit_history (cid, bid, product_views)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE product_views = product_views + 1;
        """, (cid, bid))
        db.commit()
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
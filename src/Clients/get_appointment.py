from flask import jsonify, Blueprint
from flask_login import login_required, current_user
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

get_appointment = Blueprint('get_appointment', __name__)


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


@get_appointment.route("/api/clients/appointment/<int:aid>", methods=["GET"])
@login_required
def get_appointment_details(aid):
    db = None
    cursor = None
    
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor(dictionary=True)
        
        query = """
        SELECT 
            a.aid,
            a.cid,
            a.eid,
            a.sid,
            a.start_time,
            a.expected_end_time,
            a.end_time,
            s.name as service_name,
            s.price as service_price,
            s.duration as service_duration,
            u_employee.first_name as employee_first_name,
            u_employee.last_name as employee_last_name,
            u_customer.first_name as customer_first_name,
            u_customer.last_name as customer_last_name,
            b.name as business_name,
            b.bid,
            addr.street,
            addr.city,
            addr.state,
            addr.country,
            addr.zip_code
        FROM appointments a
        JOIN services s ON a.sid = s.sid
        JOIN employee e ON a.eid = e.eid
        JOIN users u_employee ON e.uid = u_employee.uid
        JOIN customers c ON a.cid = c.cid
        JOIN users u_customer ON c.uid = u_customer.uid
        JOIN business b ON e.bid = b.bid
        LEFT JOIN addresses addr ON b.aid = addr.aid
        WHERE a.aid = %s
        """
        
        cursor.execute(query, (aid,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"message": "Appointment not found."}), 404
        # Format the response
        appointment_data = {
            "id": result['aid'],
            "customer_id": result['cid'],
            "employee_id": result['eid'],
            "service_id": result['sid'],
            "business_id": result['bid'],
            "client": f"{result['customer_first_name']} {result['customer_last_name']}",
            "worker": f"{result['employee_first_name']} {result['employee_last_name']}",
            "service": result['service_name'],
            "price": float(result['service_price']) if result['service_price'] else 0,
            "duration": result['service_duration'],
            "date": result['start_time'].strftime('%b %d, %Y') if result['start_time'] else "",
            "time": result['start_time'].strftime('%I:%M %p') if result['start_time'] else "",
            "start_time": result['start_time'].isoformat() if result['start_time'] else None,
            "expected_end_time": result['expected_end_time'].isoformat() if result['expected_end_time'] else None,
            "end_time": result['end_time'].isoformat() if result['end_time'] else None,
            "status": "Completed" if result['end_time'] else "Scheduled",
            "business_name": result['business_name'],
            "address": {
                "street": result['street'],
                "city": result['city'],
                "state": result['state'],
                "country": result['country'],
                "zip_code": result['zip_code']
            }
        }
        
        return jsonify(appointment_data), 200
        
    except mysql.connector.Error as err:
        print(f"Error fetching appointment: {err}")
        return jsonify({"message": "Failed to fetch appointment details."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

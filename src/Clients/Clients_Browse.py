from flask import jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os


load_dotenv()


client_browse = Blueprint('clients_browse', __name__)


db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()


#clients can browse salons
@client_browse.route("/api/client/browse-salons", methods=["GET"])
def browse_salons():
    query = """ 
SELECT b.bid, b.name, a.street, 
a.city, a.state, a.country, a.zip_code
 FROM business b JOIN addresses a ON b.aid = a.aid
 """
    cursor.execute(query)
    rows = cursor.fetchall()
    salons = [{"business_id": row[0], "name": row[1], 
               "street": row[2], "city": row[3], "state": row[4], 
                "country": row[5], "zip_code": row[6]} for row in rows]
    return jsonify(salons)


#clients can browse workers
@client_browse.route("/api/client/browse-workers", methods=["GET"])
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
    cursor.execute(query)
    rows = cursor.fetchall()    
    workers = [{"employee_id": row[0], "employee_first_name": row[1], 
                "employee_last_name": row[2], "expertise": row[3],
                "business_name": row[4], "business_id": row[5],
                "street": row[6], "city": row[7], "state": row[8],
                "country": row[9]
, "zip_code": row[10]
                } for row in rows]
    return jsonify(workers)


#clients can browse previous appointments
@client_browse.route("/api/clients/view-prev-appointments", methods=["GET"])
def client_view_appoints():
    query = """ 
select a.aid as appointment_id, s.name as service_name, s.price as service_price, u.first_name, 
u.last_name, e.eid as employee_id, a.start_time, a.expected_end_time, a.end_time
from appointments a
join employee e on a.eid = e.eid
join services s on a.sid = s.sid
join users u on e.uid = u.uid

"""

    cursor.execute(query)
    rows = cursor.fetchall()
    appointments = [{"appointment_id": row[0], "service_name": row[1], 
                "service_price": row[2], "employee_first_name": row[3],
                "employee_last_name": row[4], "employee_id": row[5],
                "start_time": row[6], "expected_end_time": row[7],
                "end_time": row[8]
                } for row in rows]
    return jsonify(appointments)




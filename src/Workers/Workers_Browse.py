from flask import  jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os


load_dotenv()

workers_browse = Blueprint('workers', __name__)


db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()


#workers can browse previous appointments
@workers_browse.route("/api/workers/view-prev-appointments", methods=["GET"])
def worker_view_appoints():
    query = """ 
select a.aid as appointment_id, s.name as service_name, s.price as service_price, u.first_name, 
u.last_name, c.cid as customer_id, a.start_time, a.expected_end_time, a.end_time
from appointments a
join customers c on a.cid = c.cid
join services s on a.sid = s.sid
join users u on c.uid = u.uid
"""
    cursor.execute(query)
    rows = cursor.fetchall()    
    appointments = [{"appointment_id": row[0], "service_name": row[1], 
                "service_price": row[2], "first_name": row[3],
                "last_name": row[4], "customer_id": row[5],
                "start_time": row[6], "expected_end_time": row[7],
                "end_time": row[8]
                } for row in rows]
    return jsonify(appointments)




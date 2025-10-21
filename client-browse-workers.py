from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()



app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()
#clients can browse workers
@app.route("/api/client/browse-workers", methods=["GET"])
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
    workers = [{"employee_id": row[0], "first_name": row[1], 
                "last_name": row[2], "expertise": row[3],
                "business_name": row[4], "business_id": row[5],
                "street": row[6], "city": row[7], "state": row[8],
                "country": row[9]
, "zip_code": row[10]
                } for row in rows]
    return jsonify(workers)

 






if __name__ == "__main__":
    app.run(debug=True)

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
#clients can browse salons
@app.route("/api/client/browse-salons", methods=["GET"])
def browse_salons():
    query = """ 
SELECT b.bid, b.name, a.street, 
a.city, a.state, a.country
 FROM business b JOIN addresses a ON b.aid = a.aid
 """
    cursor.execute(query)
    rows = cursor.fetchall()
    salons = [{"business_id": row[0], "name": row[1], 
               "street": row[2], "city": row[3], "state": row[4], 
               "country": row[5]} for row in rows]
    return jsonify(salons)






if __name__ == "__main__":
    app.run(debug=True)

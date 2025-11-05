from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

review_workers = Blueprint('review_workers', __name__)




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




#Clients can review workers
@review_workers.route("/api/client/review-workers", methods=["POST"])
def reviewing_workers():
    data = request.get_json()

    requirements = ["eid", "cid", "rating", "comment"]

    customer_id = data.get("cid")
    rating = data.get("rating")
    employee_id = data.get("eid")
    comment = data.get("comment")

    if not all (key in data for key in requirements):
        return jsonify({"message": "Missing one of the required fields: eid, cid, rating, comment."}), 400
    

    db = None
    cursor = None
    
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor()
        query = """ 
        insert into reviews(eid, cid, rating, comment, bid)
        values(%s, %s, %s, %s);
        """
        cursor.execute(query, (employee_id, customer_id, rating, comment))
        db.commit() 
        return jsonify({"message": "Review submitted successfully."}), 201
    except mysql.connector.Error as err:
        print(f"Error: Review submission unsuccessful. : {err}")
        if db:
            db.rollback() 
        return jsonify({"message": "Failed to submit review."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()











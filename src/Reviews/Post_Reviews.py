from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

post_reviews = Blueprint('post_reviews', __name__)





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



#clients can leave reviews of businesses
@post_reviews.route("/api/client/leave-business-review", methods=["POST"])
def leave_review():
    data = request.get_json()

    requirements = ["bid", "cid", "rating", "comment"]

    customer_id = data.get("cid")
    rating = data.get("rating")
    business_id = data.get("bid")
    comment = data.get("comment")

    if not all (key in data for key in requirements):
        return jsonify({"message": "Missing one of the required fields: bid, cid, rating, comment."}), 400
    

    db = None
    cursor = None
    
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor()
        query = """ 
        insert into reviews(bid, cid, rating, comment)
        values(%s, %s, %s, %s);
        """
        cursor.execute(query, (business_id, customer_id, rating, comment))
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


#users can leave reply to reviews
@post_reviews.route("/api/user/leave-reply-review", methods=["POST"])
def leave_reply():
    data = request.get_json()

    requirements = ["rvw_id", "uid","comment"]

    review_id = data.get("rvw_id")
    user_id = data.get("uid")
    comment = data.get("comment")

    if not all (key in data for key in requirements):
        return jsonify({"message": "Missing one of the required fields: rvw_id, uid, comment."}), 400

    db = None
    cursor = None       

    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor()
        query = """ 
        insert into review_replies(rvw_id, uid, comment)
        values(%s, %s, %s);
        """
        cursor.execute(query, (review_id, user_id, comment))
        db.commit() 
        return jsonify({"message": "Reply submitted successfully."}), 201
    except mysql.connector.Error as err:
        print(f"Error: Reply submission unsuccessful. : {err}")
        if db:
            db.rollback() 
        return jsonify({"message": "Failed to submit reply."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


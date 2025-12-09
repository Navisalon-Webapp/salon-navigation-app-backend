from flask import request, jsonify, Blueprint
from flask_cors import CORS
from flask_login import login_required, current_user
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
            port=int(os.getenv("DB_PORT")),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
            )
        return db
    except mysql.connector.Error as err:
        print(f"Error: Database could not connect. : {err}")
        return None



# Get business ID from current user (owner)
def get_business_id():
    uid = getattr(current_user, 'id', None)
    if not uid:
        return None
    
    db = None
    cursor = None
    try:
        db = get_db()
        if db is None:
            return None
        
        cursor = db.cursor(buffered=True)
        query = "SELECT bid FROM business WHERE uid = %s"
        cursor.execute(query, (uid,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as err:
        print(f"Error getting business ID: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def get_cid():
    uid = getattr(current_user, 'id', None)
    if uid is None:
        print("Error: No UID found in request context.")
        return None
    
    db = get_db()
    if db is None:
        print("Error: Could not establish connection to the database.")
        return None
    cursor = db.cursor(buffered=True)
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

@post_reviews.route("/api/client/get-reviews/<int:business_id>", methods=["GET"])
def get_business_reviews_public(business_id):
    db = None
    cursor = None
    
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor(dictionary=True, buffered=True)
        
        # Get reviews with customer names
        reviews_query = """
        SELECT r.rvw_id, r.rating, r.comment, r.created_at,
               u.first_name, u.last_name, r.cid
        FROM reviews r
        JOIN customers c ON r.cid = c.cid
        JOIN users u ON c.uid = u.uid
        WHERE r.bid = %s
        ORDER BY r.created_at DESC
        """
        cursor.execute(reviews_query, (business_id,))
        reviews = cursor.fetchall()
        
        # For each review, get replies
        for review in reviews:
            replies_query = """
            SELECT rr.comment, rr.created_at, u.first_name, u.last_name
            FROM review_replies rr
            JOIN users u ON rr.uid = u.uid
            WHERE rr.rvw_id = %s
            ORDER BY rr.created_at DESC
            LIMIT 1
            """
            cursor.execute(replies_query, (review['rvw_id'],))
            reply = cursor.fetchone()
            
            if reply:
                review['reply'] = {
                    'text': reply['comment'],
                    'createdAt': reply['created_at'].isoformat() if reply['created_at'] else None,
                    'ownerName': f"{reply['first_name']} {reply['last_name']}"
                }
            else:
                review['reply'] = None
        
        # Format response
        formatted_reviews = [{
            'id': str(r['rvw_id']),
            'reviewerName': f"{r['first_name']} {r['last_name']}",
            'rating': r['rating'],
            'comment': r['comment'],
            'createdAt': r['created_at'].isoformat() if r['created_at'] else None,
            'reply': r['reply']
        } for r in reviews]
        
        return jsonify(formatted_reviews), 200
        
    except mysql.connector.Error as err:
        print(f"Error fetching reviews: {err}")
        return jsonify({"message": "Failed to fetch reviews."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

# Get reviews for a business with replies
@post_reviews.route("/api/owner/get-business-reviews", methods=["GET"])
@login_required
def get_business_reviews():
    bid = get_business_id()
    
    if not bid:
        return jsonify({"message": "Business not found for current user."}), 404
    
    db = None
    cursor = None
    
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor(dictionary=True, buffered=True)
        
        # Get reviews with customer names
        reviews_query = """
        SELECT r.rvw_id, r.rating, r.comment, r.created_at,
               u.first_name, u.last_name, r.cid
        FROM reviews r
        JOIN customers c ON r.cid = c.cid
        JOIN users u ON c.uid = u.uid
        WHERE r.bid = %s
        ORDER BY r.created_at DESC
        """
        cursor.execute(reviews_query, (bid,))
        reviews = cursor.fetchall()
        
        # For each review, get replies
        for review in reviews:
            replies_query = """
            SELECT rr.comment, rr.created_at, u.first_name, u.last_name
            FROM review_replies rr
            JOIN users u ON rr.uid = u.uid
            WHERE rr.rvw_id = %s
            ORDER BY rr.created_at DESC
            LIMIT 1
            """
            cursor.execute(replies_query, (review['rvw_id'],))
            reply = cursor.fetchone()
            
            if reply:
                review['reply'] = {
                    'text': reply['comment'],
                    'createdAt': reply['created_at'].isoformat() if reply['created_at'] else None,
                    'ownerName': f"{reply['first_name']} {reply['last_name']}"
                }
            else:
                review['reply'] = None
        
        # Format response
        formatted_reviews = [{
            'id': str(r['rvw_id']),
            'reviewerName': f"{r['first_name']} {r['last_name']}",
            'rating': r['rating'],
            'comment': r['comment'],
            'createdAt': r['created_at'].isoformat() if r['created_at'] else None,
            'reply': r['reply']
        } for r in reviews]
        
        return jsonify(formatted_reviews), 200
        
    except mysql.connector.Error as err:
        print(f"Error fetching reviews: {err}")
        return jsonify({"message": "Failed to fetch reviews."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


#clients can leave reviews of businesses
@post_reviews.route("/api/client/leave-business-review", methods=["POST"])
def leave_review():
    data = request.get_json()

    requirements = ["bid", "cid", "rating", "comment"]

    uid = data.get("cid")
    cid = get_cid()
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
    
        cursor = db.cursor(buffered=True)
        query = """ 
        insert into reviews(bid, cid, rating, comment)
        values(%s, %s, %s, %s);
        """
        cursor.execute(query, (business_id, cid, rating, comment))
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
@login_required
def leave_reply():
    data = request.get_json()

    requirements = ["rvw_id", "comment"]

    review_id = data.get("rvw_id")
    user_id = getattr(current_user, 'id', None)
    comment = data.get("comment")

    if not all (key in data for key in requirements):
        return jsonify({"message": "Missing one of the required fields: rvw_id, comment."}), 400
    
    if not user_id:
        return jsonify({"message": "User not authenticated."}), 401

    db = None
    cursor = None       

    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor(buffered=True)
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


from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import current_user, login_required


load_dotenv()

manage_cart = Blueprint('manage_cart', __name__)





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

#get current logged-in client's customer id
def get_cid():
    uid = getattr(current_user, 'id', None)
    if uid is None:
        print("Error: No UID found in request context.")
        return None
    
    db = get_db()
    if db is None:
        print("Error: Could not establish connection to the database.")
        return None
    cursor = db.cursor()
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
    


#Clients can view their cart
@manage_cart.route("/api/clients/view-cart", methods=["GET"])
@login_required #can only be accessed by logged in users
def view_cart():
    
    
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
        
        customer_id = get_cid()
        if customer_id is None:
            return jsonify({"message": "Could not retrieve customer ID."}), 500
        
        cursor = db.cursor()

        
        query = """
        select c.cart_id, c.pid, p.name, p.price, c.amount, (p.price * c.amount) as total,
               b.name as business_name, p.image
        from cart c 
        join products p on c.pid = p.pid
        join business b on p.bid = b.bid
        where c.cid = %s;
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        cart_items = []
        for row in results:
            cart_id, pid, name, price, amount, total, business_name, image = row
            cart_items.append({
                "cart_id": cart_id,
                "pid": pid,
                "name": name,
                "price": float(price),
                "amount": amount,
                "total": float(total),
                "business_name": business_name,
                "image": image.decode('utf-8') if image else None
            })
        return jsonify({"cart_items": cart_items}), 200
    except mysql.connector.Error as err:
        print(f"Error: Could not retrieve cart items. : {err}")
        return jsonify({"message": "Could not retrieve cart items."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


#Clients can alter the amount of a specific item in their cart
@manage_cart.route("/api/clients/alter-cart/<int:cart_id>", methods=["PUT"])
@login_required
def alter_cart_item(cart_id):
    data = request.get_json()
    new_amount = data.get("amount")
    if new_amount is None:
        return jsonify({"message": "New amount is required."}), 400

    db = None
    cursor = None
    try:

        customer_id = get_cid()
        if customer_id is None:
            return jsonify({"message": "Could not retrieve customer ID."}), 500
        
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
        
        

        cursor = db.cursor()

        query = """
        update cart
        set amount = %s
        where cart_id = %s;
        """
        cursor.execute(query, (new_amount, cart_id))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "No cart item found with the given cart_id."}), 404

        return jsonify({"message": "Cart item updated successfully."}), 200
    except mysql.connector.Error as err:
        print(f"Error: Could not update cart item. : {err}")
        return jsonify({"message": "Could not update cart item."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
            
       


# Clients can checkout (clear cart)
@manage_cart.route("/api/clients/checkout", methods=["POST"])
@login_required
def checkout():
    data = request.get_json()
    
    # Get payment details (for now just validate they exist)
    required_fields = ["name", "email", "cardNumber", "expiry", "cvv"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}."}), 400
    
    db = None
    cursor = None
    try:
        customer_id = get_cid()
        if customer_id is None:
            return jsonify({"message": "Could not retrieve customer ID."}), 500
        
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor()
        
        # Get cart items to process
        query = "SELECT cart_id FROM cart WHERE cid = %s"
        cursor.execute(query, (customer_id,))
        cart_items = cursor.fetchall()
        
        if not cart_items:
            return jsonify({"message": "Cart is empty."}), 400
        
        # Clear the cart (in a real app, you'd create an order record first)
        delete_query = "DELETE FROM cart WHERE cid = %s"
        cursor.execute(delete_query, (customer_id,))
        db.commit()
        
        return jsonify({
            "message": "Order placed successfully! Come in store for pickup.",
            "items_processed": len(cart_items)
        }), 200
        
    except mysql.connector.Error as err:
        print(f"Error: Could not process checkout. : {err}")
        if db:
            db.rollback()
        return jsonify({"message": "Could not process checkout."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

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
        select c.cart_id, c.pid, p.name, p.price, c.amount, (p.price * c.amount) as total
        from cart c join products p on c.pid = p.pid
        where c.cid = %s;
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        cart_items = []
        for (cart_id, pid, name, price, amount, total) in results:
            cart_items.append({
                "cart_id": cart_id,
                "pid": pid,
                "name": name,
                "price": float(price),
                "amount": amount,
                "total": float(total)
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
@manage_cart.route("/api/clients/alter-cart/cart_id", methods=["PUT"])
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
            
       





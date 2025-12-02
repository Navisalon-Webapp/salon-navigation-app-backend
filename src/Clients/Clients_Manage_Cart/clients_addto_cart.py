from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import  current_user, login_required


load_dotenv()

addto_cart = Blueprint('addto_cart', __name__)





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
    
    



#Clients can add items to their cart
@addto_cart.route("/api/clients/manage-carts", methods=["POST"])
@login_required #can only be accessed by logged in clients  
def add_to_cart():
    data = request.get_json()

    required_fields = ["pid","amount", "bid"]

    customer_id = get_cid()
    if customer_id is None:
        return jsonify({"message": "Could not determine customer ID for the client."}), 401 #unauthorized
    
    product_id = data.get("pid")
    amount = data.get("amount")
    business_id = data.get("bid")
    
    missing_fields = [field for field in required_fields if data.get(field) is None]
    if missing_fields:
        return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}."}), 400
    
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor()

        # Check Stock in DB before adding to cart
        check_stock_q = """
        select p.stock, coalesce(c.amount, 0) as current_amt_in_cart from products p left join cart c on p.pid = c.pid and c.cid = %s
        where p.pid = %s;
        """
        cursor.execute(check_stock_q, (customer_id, product_id))
        result = cursor.fetchone()
        if result is None:
            return jsonify({"message": "Product does not exist."}), 404
        stock, current_amt_in_cart = result
        
        if stock <= 0:
            return jsonify({"message": "Product is out of stock."}), 400

        query = """
        insert into cart(cid, pid, amount, bid)
        values(%s, %s, %s, %s)
        on duplicate key update amount = amount + VALUES(amount);
        """
        cursor.execute(query, (customer_id, product_id, amount, business_id))

        update_stock_q = """
        UPDATE products
        SET stock = stock - %s
        WHERE pid = %s AND stock >= %s;
        """
        cursor.execute(update_stock_q, (amount, product_id, amount))
        db.commit()
        return jsonify({"message": "Product added to cart successfully."}), 201
    except mysql.connector.Error as err:
        print(f"Error: Could not add product to cart. : {err}")
        return jsonify({"message": "Could not add product to cart due to a database error."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

#Clients can delete an item from their cart
@addto_cart.route("/api/clients/manage-carts/delete-cart-item/<int:cart_id>", methods=["DELETE"])
@login_required #can only be accessed by logged in clients
def delete_cart_item(cart_id):
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
        
        

        cursor = db.cursor(dictionary=True)


        #identify the item to be deleted and its amount
        item_query = """
        select pid, amount from cart
        where cart_id = %s and cid = %s;  
        """  
        cursor.execute(item_query, (cart_id, customer_id))
        item = cursor.fetchone()
        if item is None:
            return jsonify({"message": "Cart item not found."}), 404

        pid = item['pid']
        return_amount = item['amount']  


        # "put item back on the shelf" by updating the stock in products table
        update_stock_q = """
        UPDATE products p
        SET p.stock = p.stock + %s
        WHERE p.pid = %s;
        """   
        cursor.execute(update_stock_q, (return_amount, pid))

        # delete the item from cart
        delete_query = """
        delete from cart
        where cart_id = %s and cid = %s;
        """
        cursor.execute(delete_query, (cart_id, customer_id))

        db.commit()
        return jsonify({"message": "Cart item deleted successfully.Product stock updated to original amount."}), 200
    
    except mysql.connector.Error as err:
        print(f"Error: Could not delete cart item. : {err}")
        return jsonify({"message": "Could not delete cart item."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()



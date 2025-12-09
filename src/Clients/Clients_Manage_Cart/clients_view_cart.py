from flask import request, jsonify, Blueprint
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os
from flask_login import current_user, login_required

from src.LoyaltyProgram.loyalty_service import award_points_for_visit


load_dotenv()

manage_cart = Blueprint('manage_cart', __name__)





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
        
        cursor = db.cursor(buffered=True)

        
        query = """
        select c.cart_id, c.pid, p.name, p.price, c.amount, (p.price * c.amount) as total,
               b.name as business_name, b.bid, p.image
        from cart c 
        join products p on c.pid = p.pid
        join business b on p.bid = b.bid
        where c.cid = %s;
        """
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        cart_items = []
        for row in results:
            cart_id, pid, name, price, amount, total, business_name, bid, image = row
            cart_items.append({
                "cart_id": cart_id,
                "pid": pid,
                "name": name,
                "price": float(price),
                "amount": amount,
                "total": float(total),
                "business_name": business_name,
                "bid": bid,
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
    if new_amount is None or new_amount < 0:
        return jsonify({"message": "Valid amount is required."}), 400

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

        get_cart_query = """
        SELECT c.pid, c.amount as current_amount, p.stock
        FROM cart c
        JOIN products p ON c.pid = p.pid
        WHERE c.cart_id = %s AND c.cid = %s;
        """
        cursor.execute(get_cart_query, (cart_id, customer_id))
        cart_item = cursor.fetchone()

        if not cart_item:
            return jsonify({"message": "No cart item found with the given cart_id."}), 404

        pid = cart_item['pid']
        current_amount = cart_item['current_amount']
        available_stock = cart_item['stock']
        
        amount_difference = new_amount - current_amount

        if amount_difference > 0:
            if available_stock < amount_difference:
                return jsonify({"message": f"Insufficient stock. Only {available_stock} available."}), 400
            
            update_stock_query = """
            UPDATE products
            SET stock = stock - %s
            WHERE pid = %s AND stock >= %s;
            """
            cursor.execute(update_stock_query, (amount_difference, pid, amount_difference))
            
            if cursor.rowcount == 0:
                return jsonify({"message": "Failed to update stock. Insufficient stock available."}), 400

        elif amount_difference < 0:
            return_amount = abs(amount_difference)
            
            update_stock_query = """
            UPDATE products
            SET stock = stock + %s
            WHERE pid = %s;
            """
            cursor.execute(update_stock_query, (return_amount, pid))

        update_cart_query = """
        UPDATE cart
        SET amount = %s
        WHERE cart_id = %s AND cid = %s;
        """
        cursor.execute(update_cart_query, (new_amount, cart_id, customer_id))

        db.commit()

        return jsonify({"message": "Cart item updated successfully."}), 200
        
    except mysql.connector.Error as err:
        if db:
            db.rollback()
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
        
        cursor = db.cursor(dictionary=True, buffered=True)
        
        query = """
        SELECT c.cart_id, c.pid, c.amount, c.bid, p.price, p.stock, p.name
        FROM cart c
        JOIN products p ON c.pid = p.pid
        WHERE c.cid = %s
        """
        cursor.execute(query, (customer_id,))
        cart_items = cursor.fetchall()
        
        if not cart_items:
            return jsonify({"message": "Cart is empty."}), 400
        
        # Validate stock availability before processing checkout
        for item in cart_items:
            if item['stock'] < item['amount']:
                return jsonify({
                    "message": f"Not enough stock for {item['name']}. Available: {item['stock']}, Requested: {item['amount']}"
                }), 400
        
        awards = []

        for item in cart_items:
            # Decrement stock by the amount purchased
            update_stock_query = """
            UPDATE products 
            SET stock = stock - %s 
            WHERE pid = %s AND stock >= %s
            """
            cursor.execute(update_stock_query, (item['amount'], item['pid'], item['amount']))
            
            # Verify the stock was actually updated
            if cursor.rowcount == 0:
                db.rollback()
                return jsonify({
                    "message": f"Insufficient stock for {item['name']}. Please refresh and try again."
                }), 400
            
            transaction_amount = float(item['price']) * item['amount']
            insert_transaction_query = """
            INSERT INTO transactions (cid, bid, pid, amount)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_transaction_query, (
                customer_id,
                item['bid'],
                item['pid'],
                transaction_amount
            ))

            awards.append(
                {
                    "bid": item['bid'],
                    "amount": transaction_amount,
                    "quantity": item.get('amount', 1),
                }
            )
        
        delete_query = "DELETE FROM cart WHERE cid = %s"
        cursor.execute(delete_query, (customer_id,))
        
        db.commit()

        for award in awards:
            try:
                award_points_for_visit(
                    db,
                    aid=None,
                    cid=customer_id,
                    bid=award["bid"],
                    amount=award["amount"],
                    quantity=award.get("quantity"),
                    source="product",
                )
            except Exception as err:
                print(f"[WARN] Failed to award loyalty for product purchase: {err}")
        
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

@manage_cart.route("/api/client/business-products/<int:business_id>", methods=["GET"])
def get_business_products(business_id):
    db = None
    cursor = None
    
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500
        
        cursor = db.cursor(dictionary=True, buffered=True)
        
        products_query = """
        SELECT pid, name as product_name, description, price, stock, image
        FROM products
        WHERE bid = %s
        ORDER BY name
        """
        cursor.execute(products_query, (business_id,))
        products = cursor.fetchall()
        
        for product in products:
            if product['price'] is not None:
                product['price'] = float(product['price'])
            if product['image'] is not None:
                product['image'] = product['image'].decode('utf-8')
        
        return jsonify(products), 200
        
    except mysql.connector.Error as err:
        print(f"Error fetching products: {err}")
        return jsonify({"message": "Failed to fetch products."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
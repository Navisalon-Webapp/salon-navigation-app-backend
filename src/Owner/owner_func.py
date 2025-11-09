import os
import base64
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from .queries import *

load_dotenv()

def get_db_connection():
    """create database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_salon_details_by_uid(uid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(get_salon_details, [uid])
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def update_salon_details_by_uid(uid, name, status, street, city, state, zip_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(update_salon_basic, [name, status, uid])
    cursor.execute(update_salon_address, [street, city, state, zip_code, uid])
    
    conn.commit()
    cursor.close()
    conn.close()

def get_products_by_bid(bid):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(get_salon_products, (bid,))
        products = cursor.fetchall()
        
        for product in products:
            if product.get('image'):
                image_data = product['image'].decode('utf-8') if isinstance(product['image'], bytes) else product['image']
                product['image'] = image_data
            else:
                product['image'] = None
        
        return products
    except Error as e:
        print(f"Error fetching products: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def add_product(bid, name, price, stock, description=None, image=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(create_product, [bid, name, price, stock, description, image])
    conn.commit()
    pid = cursor.lastrowid
    cursor.close()
    conn.close()
    return pid

def update_product_stock_by_pid(pid, stock):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(update_product_stock, [stock, pid])
    conn.commit()
    cursor.close()
    conn.close()

def get_product_by_id(pid):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(get_product_by_id_query, (pid,))
        product = cursor.fetchone()
        
        if product and product.get('image'):
            image_data = product['image'].decode('utf-8') if isinstance(product['image'], bytes) else product['image']
            product['image'] = image_data
        
        return product
    except Error as e:
        print(f"Error fetching product: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_product_by_pid(pid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(delete_product_query, [pid])
    conn.commit()
    cursor.close()
    conn.close()

def get_curr_bid():
    from flask_login import current_user
    uid = getattr(current_user, "id", None)
    if uid is None:
        raise ValueError("Current user is not logged in")

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT bid FROM business WHERE uid = %s", (uid,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row or row["bid"] is None:
            raise ValueError("Business ID not found for current user")
        return row["bid"]
    except Exception as e:
        conn.close()
        raise e



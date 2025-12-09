import os
import base64
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def get_db_connection():
    """create database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            port=int(os.getenv("DB_PORT")),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_curr_bid():
    from flask_login import current_user
    uid = getattr(current_user, "id", None)
    if uid is None:
        raise ValueError("Current user is not logged in")

    conn = get_db_connection()
    if conn is None:
        raise ValueError("Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
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
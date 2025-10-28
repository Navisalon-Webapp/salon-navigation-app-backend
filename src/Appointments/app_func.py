import os
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
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
    

def get_cid_for_uid(conn, uid):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT cid FROM customers WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    return row['cid'] if row else None
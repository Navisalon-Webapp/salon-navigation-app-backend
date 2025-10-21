import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import re

load_dotenv()

def get_db_connection():
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
    
def valid_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return True if re.match(pattern, email) else False


def verify_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customer_id FROM customer where email =  %s limit 1;", [email])
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return False if result is None else True

def verify_confirmPass(password, confirmPassword):
    return True if password==confirmPassword else False

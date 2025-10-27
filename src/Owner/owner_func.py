import os
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
    
def get_business_info(uid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query_business_info,[uid])
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

def update_salon(data):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    param = [data['firstName'],data['lastName'],data['phoneNumber'],data['uid']]
    cursor.execute(update_user_info, param)
    param = [data['salonStreet'], data['salonCity'],data['salonState'],data['salonCountry'],data['salonZipCode'],data['uid']]
    cursor.execute(update_adress,param)
    param = [data['salonName'],data['uid']]
    cursor.execute(update_business_name,param)
    conn.commit()
    cursor.close()
    conn.close()

    

import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from .queries import query_user_info
import hashlib
import secrets
import re

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
    
def valid_email(email):
    """Verify email has valid format"""
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return True if re.match(pattern, email) else False

def verify_email(email):
    """Check if email already exists in authenticate table"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT uid FROM authenticate where email =  %s limit 1;", [email])
        result = cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return False if result is None else True

def verify_confirmPass(password, confirmPassword):
    """Verify password and confirm password are equal"""
    return True if password==confirmPassword else False

def insert_address(data):
    """insert address in addresses table for business"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        param=[data['salonAddress'], data['salonCity'], data['salonState'], data['salonCountry'], data['salonZipCode']]
        cursor.execute("INSERT INTO addresses (street, city, state, country, zip_code) VALUES (%s, %s, %s, %s, %s);",param)
        aid = cursor.lastrowid
        conn.commit()
        return aid
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        cursor.close()
        conn.close()

def new_salt():
    salt = secrets.token_hex(16)
    return salt

def hash_pass(password,salt):
    """return hash(password+salt)

    salt and hash password
    """
    h = hashlib.new("SHA256")
    h.update(password.encode())
    h.update(salt.encode())
    return (h.hexdigest())

def insert_Auth(firstName, lastName, email, password):
    """return uid

    insert user first and last name into users table

    insert email, password hash, and salt into authenticate table
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("INSERT INTO users (first_name, last_name) VALUES (%s, %s);",[firstName, lastName])
        uid = cursor.lastrowid

        salt = new_salt()
        hash = hash_pass(password, salt)

        param = [uid, email, hash, salt]
        cursor.execute("INSERT INTO authenticate (uid, email, pw_hash, salt) VALUES (%s, %s, %s, %s);", param)

        conn.commit()
        return uid
    except Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
def insert_Customer(uid):
    """return cid

    insert uid into customers table

    insert uid and 1 into users_roles table
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("INSERT INTO customers (uid) VALUES (%s);",[uid])
        cid = cursor.lastrowid
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,1])
        conn.commit()
        return cid
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def insert_Owner(uid, data):
    """return bid

    update users table with phone

    insert uid into business table

    insert uid and 2 into users_roles table
    """
    conn =  None
    cursor = None
    try:
        aid = insert_address(data)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE users SET phone = %s WHERE uid = %s;", [data['phoneNumber'], uid])
        param = [uid, data['salonName'], aid]
        cursor.execute("INSERT INTO business (uid, name, aid) VALUES (%s, %s, %s);",param)
        bid = cursor.lastrowid
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,2])
        conn.commit()
        return bid
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        print(f"Database Error {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def insert_Worker(uid, data):
    """return eid

    update users table with phone

    check if salon exists and retreive bid if it does

    insert uid into employee table

    insert uid and 3 into users_roles table
    
    insert expertise into employee_expertise table
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE users SET phone = %s WHERE uid = %s;", [data['phoneNumber'], uid])
        cursor.execute("SELECT bid FROM business WHERE name = %s;", [data['salonName']])
        result = cursor.fetchone()
        param = [uid]
        if(result is None):
            cursor.execute("INSERT INTO employee (uid) VALUES (%s);",param)
        else:
            param += [result['bid']]
            cursor.execute("INSERT INTO employee (uid, bid) VALUES (%s, %s);",param)
        eid = cursor.lastrowid
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,3])
        
        # Insert expertise into database
        if 'specialty' in data and data['specialty']:
            # First check if the expertise exists
            cursor.execute("SELECT exp_id FROM expertise WHERE expertise = %s;", [data['specialty']])
            expertise_result = cursor.fetchone()
            
            if expertise_result:
                # Expertise exists, use its exp_id
                exp_id = expertise_result['exp_id']
            else:
                # Expertise doesn't exist, create it
                cursor.execute("INSERT INTO expertise (expertise) VALUES (%s);", [data['specialty']])
                exp_id = cursor.lastrowid
            
            # Link employee to expertise
            cursor.execute("INSERT INTO employee_expertise (eid, exp_id) VALUES (%s, %s);", [eid, exp_id])
        
        conn.commit()
        return eid
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def insert_Admin(uid):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,4])
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#sign in functions
def get_Auth(email):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM authenticate WHERE email = %s", [email])
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_pass(email, password):
    auth = get_Auth(email)
    if(hash_pass(password,auth['salt']) != auth['pw_hash']):
        return False
    else:
        return True
    

    
def get_uid(email):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT uid FROM authenticate WHERE email = %s", [email])
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_info(uid):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_user_info,[uid])
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_role(uid):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM roles LEFT JOIN users_roles ON roles.rid=users_roles.rid WHERE uid = %s", [uid])
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_email_sub(cid):
    if not cid:
        print ("no uid")
        return
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("INSERT INTO email_subscription (cid, promotion, appointment) VALUES (%s, true, true)",[cid])
        id = cursor.lastrowid
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    # return id
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from .queries import query_user_info, update_password
import hashlib
import secrets
import re
from flask import jsonify

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
    
def insert_Customer(uid, data):
    """return cid

    insert uid into customers table

    insert uid and 1 into users_roles table
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE users SET phone = %s WHERE uid = %s;", [data['phoneNumber'], uid])
        cursor.execute("INSERT INTO customers (uid, birthdate, gender, ind_id, income) VALUES (%s, %s, %s, %s, %s);",[uid, data['birthDate'], data['gender'], data['industry'], data['income']])
        cid = cursor.lastrowid
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,1])
        conn.commit()
        return cid
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Error creating customer: {str(e)}")
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
        param = [uid, data['salonName'], aid, data['salonEstYear']]
        cursor.execute("INSERT INTO business (uid, name, aid, year_est) VALUES (%s, %s, %s, %s);",param)
        bid = cursor.lastrowid
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,2])
        conn.commit()
        return bid
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Error creating owner: {str(e)}")
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
    
    insert services into employee_services table
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE users SET phone = %s WHERE uid = %s;", [data['phoneNumber'], uid])
        cursor.execute("SELECT bid, status FROM business WHERE name = %s;", [data['salonName']])
        result = cursor.fetchone()
        param = [uid]
        if(result is None):
            cursor.execute("INSERT INTO employee (uid) VALUES (%s);",param)
        else:
            # Check if business is approved before allowing employee to join
            if not result['status']:
                raise Exception("Cannot join salon - business is not yet approved by admin")
            param += [result['bid'], data['startYear']]
            cursor.execute("INSERT INTO employee (uid, bid, start_year) VALUES (%s, %s, %s);",param)
        eid = cursor.lastrowid
        cursor.execute("INSERT INTO users_roles (uid, rid) VALUES (%s, %s);",[uid,3])
        
        if 'service' in data and data['service']:
            cursor.execute("INSERT INTO services (name, cat_id) VALUES (%s, %s)", [data['service'], data['serviceCat']])
            sid = cursor.lastrowid
            
            # Link employee to service
            cursor.execute("INSERT INTO employee_services (eid, sid) VALUES (%s, %s);", [eid, sid])
        
        conn.commit()
        return eid
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Error creating worker: {str(e)}")
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

def inc_new_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO new_users_monthly (year, month, new_users_count)
            VALUES (YEAR(CURDATE()), MONTH(CURDATE()), 1)
            ON DUPLICATE KEY UPDATE new_users_count = new_users_count + 1
        """)
        conn.commit()
    finally:
        cursor.close()
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
    
def update_pass(email, password):
    conn = None
    cursor = None
    
    try:
        salt = new_salt()
        hash = hash_pass(password, salt)
        param = [hash, salt, email]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_password, param)
        conn.commit()
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

def update_active(uid):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE users SET last_active = NOW() WHERE uid = %s", (uid,),)
        cursor.execute("""
            INSERT INTO active_users_monthly (year, month, active_count)
            VALUES (YEAR(CURDATE()), MONTH(CURDATE()), 1)
            ON DUPLICATE KEY UPDATE active_count = active_count + 1
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    
    return jsonify({"status": "success", "user": uid}), 200

def check_business_approval(uid):
    """Check if a business account has been approved by admin"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT status FROM business WHERE uid = %s
        """, (uid,))
        result = cursor.fetchone()
        return result['status'] if result else False
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return False
    except Exception as e:
        print(f"Error {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_employee_approval(uid):
    """Check if an employee account has been approved by their salon"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT approved FROM employee WHERE uid = %s
        """, (uid,))
        result = cursor.fetchone()
        return result['approved'] if result else False
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return False
    except Exception as e:
        print(f"Error {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

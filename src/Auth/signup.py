from flask import Blueprint, request, jsonify
from .auth_func import  *

signup = Blueprint("signup", __name__, url_prefix='')

@signup.route('/customer/signup', methods=['POST'])
def getClientSignUp():
    try:
        data=request.get_json()

        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            }), 400
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            }), 409
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            }), 400

        uid = insert_Auth(data['firstName'],data['lastName'],data['email'],data['password'])
        if not isinstance(uid, int):
            raise Exception("Failed to create user account")
        print(uid)
        cid = insert_Customer(uid, data)
        print(cid)
        if not isinstance(cid, int):
            raise Exception("Failed to create customer record")

        create_email_sub(cid)
        inc_new_users()

        return jsonify({
            "status": "success",
            "message": "Added new customer to database",
            "User_ID": uid,
            "Customer_ID":cid
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@signup.route('/business/signup', methods=['POST'])
def getBusinessSignUp():
    try:
        data=request.get_json()
        # print(data)
        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            }), 400
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            }), 409
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            }), 400
        print(data)
        uid = insert_Auth(data['firstName'],data['lastName'],data['email'],data['password'])
        print("test")
        bid = insert_Owner(uid, data)
        print(uid)

        inc_new_users()

        return jsonify({
            "status": "success", 
            "message": "Added new business to database",
            "User_ID": uid,
            "Business_ID": bid
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@signup.route('/employee/signup', methods=['POST'])
def getEmployeeSignUp():
    try:
        data=request.get_json()
        # print(data)
        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            }), 400
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            }), 409
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            }), 400
        
        uid = insert_Auth(data['firstName'],data['lastName'],data['email'],data['password'])
        eid = insert_Worker(uid, data)
        inc_new_users()

        return jsonify({
            "status": "success",
            "message": "Added new employee to database",
            "User_ID": uid,
            "Employee_ID":eid
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@signup.route('/admin/signup', methods=['POST'])
def getAdminSignUp():
    try:
        data=request.get_json()
        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            }), 400
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            }), 409
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            }), 400
        
        uid = insert_Auth(data['firstName'],data['lastName'],data['email'],data['password'])
        insert_Admin(uid)
        inc_new_users()
        return jsonify({
            "status": "success",
            "message": "Added new admin to database",
            "User_ID": uid
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@signup.route('/list-business', methods=['GET'])
def business_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT uid, bid, name FROM business")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200

@signup.route('/list-services', methods=['GET'])
def service_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sid, name FROM services")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200

@signup.route('/list-service-categories', methods=['GET'])
def service_category_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cat_id, name FROM service_categories")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200

@signup.route('/list-industries', methods=['GET'])
def industry_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ind_id, name FROM industries")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200
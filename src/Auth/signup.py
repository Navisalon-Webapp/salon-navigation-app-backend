from flask import Blueprint, request, jsonify
from .auth_func import verify_email, verify_confirmPass, valid_email

signup = Blueprint("signup", __name__, url_prefix='')

@signup.route('/customer/signup', methods=['POST'])
def getClientSignUp():
    try:
        data=request.get_json()
        # print(data)
        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            })
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            })
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            })
            
        
        return jsonify({
            "status": "success", 
            "message": "Customer signup received",
            "received_data": data
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@signup.route('/owner/signup', methods=['POST'])
def getOwnerSignUp():
    try:
        data=request.get_json()
        # print(data)
        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            })
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            })
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            })

        return jsonify({
            "status": "success", 
            "message": "Customer signup received",
            "received_data": data
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@signup.route('/worker/signup', methods=['POST'])
def getWorkerSignUp():
    try:
        data=request.get_json()
        # print(data)
        if(valid_email(data['email'])==False):
            return jsonify({
                "status": "failure",
                "message": "invalid email address",
                "invalid_email": data['email']
            })
        if(verify_email(data['email'])):
            return jsonify({
                "status": "failure",
                "message": "customer email already exists",
                "existing_email": data['email']
            })
        if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
            return jsonify({
                "status": "failure",
                "message": "passwords do not match",
                "password": data['password'],
                "confirmPassword": data['confirmPassword']
            })

        return jsonify({
            "status": "success", 
            "message": "Customer signup received",
            "received_data": data
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
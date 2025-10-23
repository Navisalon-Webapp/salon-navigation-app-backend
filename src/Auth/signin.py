from flask import Blueprint, request, jsonify
from .auth_func import  *
from .User import *

signin = Blueprint("signin", __name__, url_prefix='')

@signin.route('/signin',methods=['POST'])
def getSignin():
    try:
        data = request.get_json()
        if(not data['email'] or not data['password']):
            print("sign in fields not fulfilled")
            return jsonify({
                "status": "failure",
                "message": "missing username or password",
                "missing_value": "email" if not data['email'] else "password"
            })
        if(valid_email(data['email']) == False):
            print("email is not valid")
            return jsonify({
                "status":"failure",
                "message":"invalid email address",
                "email": data['email']
            })
        if(verify_email(data['email']) == False):
            print("email does not exist")
            return jsonify({
                "status":"failure",
                "message":"no account associated with email",
                "email": data['email']
            })
        if(verify_pass(data['email'], data['password']) == False):
            print("wrong password")
            return jsonify({
                "status":"failure",
                "message":"password is incorrect",
                "password": data['password']
            })
        uid = get_uid(data['email'])
        user = load_user(uid, remember=True)
        print("account verified")
        return jsonify({
            "status":"success",
            "message":"signed in",
            "User_ID": uid['uid'],
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
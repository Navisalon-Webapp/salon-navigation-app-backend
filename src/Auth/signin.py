from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .auth_func import  *
from .User import User

signin = Blueprint("signin", __name__, url_prefix='')

@signin.route('/signin',methods=['POST'])
def getSignin():
    try:
        data = request.get_json()
        print(type(data))
        if(not data['email'] or not data['password']):
            print("sign in fields not fulfilled")
            return jsonify({
                "status": "failure",
                "message": "missing username or password",
                "missing_value": "email" if not data['email'] else "password"
            }), 400
        if(valid_email(data['email']) == False):
            print("email is not valid")
            return jsonify({
                "status":"failure",
                "message":"invalid email address",
                "email": data['email']
            }), 400
        if(verify_email(data['email']) == False):
            print("email does not exist")
            return jsonify({
                "status":"failure",
                "message":"no account associated with email",
                "email": data['email']
            }), 401
        if(verify_pass(data['email'], data['password']) == False):
            print("wrong password")
            return jsonify({
                "status":"failure",
                "message":"password is incorrect",
                "password": data['password']
            }), 401
        
        uid = get_uid(data['email'])
        user_info = get_user_info(uid['uid'])
        user = User(
            id = user_info['uid'],
            email = user_info['email'],
            firstName = user_info['first_name'],
            lastName = user_info['last_name'],
            role = user_info['name']
        )
        login_user(user, remember=False)

        print("account verified")
        return jsonify({
            "status":"success",
            "message":"signed in",
            "User_ID": current_user.id,
            "role": current_user.role
        }), 200
    except Exception as e:
        print("error", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    
@signin.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({
        'message': 'Logout successful'
    }), 200

@signin.route('/user-session', methods=['GET'])
@login_required
def get_user_session():
    return jsonify({
        "User_ID": current_user.id,
        "email": current_user.id,
        "first name": current_user.firstName,
        "last name": current_user.lastName,
        "role": current_user.role
    })

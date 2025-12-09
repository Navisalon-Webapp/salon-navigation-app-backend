from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from helper.utils import get_curr_eid
from .auth_func import  *
from .User import User
from src.Notifications.notification_func import send_password_reset
from helper.utils import get_email, check_role, get_curr_bid, get_curr_cid, get_curr_eid

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
        update_active(user_info['uid'])
        employee_id = None
        if current_user.role == "employee":
            try:
                employee_id = str(get_curr_eid())
            except Exception as e:
                print(f"Failed to resolve employee id during signin: {e}")

        print("account verified")
        return jsonify({
            "status":"success",
            "message":"signed in",
            "User_ID": current_user.id,
            "role": current_user.role,
            "employee_id": employee_id
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

@signin.route('/password-reset/email', methods=['POST'])
def reset_password_email():
    data = request.get_json()
    email = data['email'] if data['email'] else None

    if not email:
        print("Email required")
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        }), 400
    if(valid_email(email) == False):
        print("email is not valid")
        return jsonify({
            "status":"failure",
            "message":"invalid email address",
            "email": email
        }), 400
    if(verify_email(email) == False):
        print("email does not exist")
        return jsonify({
            "status":"failure",
            "message":"no account associated with email",
            "email": data['email']
        }), 401
    uid = get_uid(email)
    # Return the uid so frontend can redirect directly to reset page
    return jsonify({
        "status":"success",
        "message":"email verified",
        "uid": uid['uid']
    }), 200

@signin.route('/password-reset', methods=['POST'])
def reset_password():
    data = request.get_json()
    uid = data['uid'] if data['uid'] else None
    password = data['password'] if data['password'] else None
    confirmPassword = data['confirmPassword'] if data['confirmPassword'] else None

    if not password or not confirmPassword or not uid:
        print("Missing parameters")
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        }), 400
    email = get_email(uid)

    if(verify_pass(email, password) == True):
        print("Password is same as original")
        return jsonify({
            "status":"failure",
            "message":"password must be different from current password"
        }), 400
    if(verify_confirmPass(data['password'],data['confirmPassword'])==False):
        print("passwords do not match")
        return jsonify({
            "status": "failure",
            "message": "passwords do not match",
            "password": data['password'],
            "confirmPassword": data['confirmPassword']
        }), 400
    update_pass(email, password)
    return jsonify({
        "status":"success",
        "message":"password reset",
        "email":email
    }), 200
    
@signin.route('/user-session', methods=['GET'])
@login_required
def get_user_session():
    payload = {
        "User_ID": current_user.id,
        "email": current_user.email,
        "first name": current_user.firstName,
        "last name": current_user.lastName,
        "role": current_user.role
    }
    role = current_user.role
    if role == 'customer':
        payload['customer_id'] = get_curr_cid()
    elif role == 'business':
        payload['business_id'] = get_curr_bid()
    elif role == 'employee':
        payload['employee_id'] = get_curr_eid()
    elif role == 'admin':
        pass
    else:
        logout_user()
        return jsonify({
            "status":"failure",
            "message":"account error",
            "action": "logged out"
        }), 401
    return jsonify(payload), 200

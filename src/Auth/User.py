from flask_login import LoginManager, UserMixin
from .auth_func import  get_user_info
from mysql.connector import Error
import mysql.connector

login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, uid, email, firstName, lastName, role):
        self.uid=uid
        self.email=email
        self.firstName=firstName
        self.lastName=lastName
        self.role=role

@login_manager.user_loader
def load_user(uid):
    user_info = get_user_info(uid)
    if user_info:
        return User(
            uid=user_info['uid'],
            email=user_info['email'],
            firstName=user_info['first_name'],
            lastName=user_info['last_name'],
            role=user_info['name']
        )
    
@login_manager.unauthorized_handler
def unauthorized():
    from flask import jsonify
    return jsonify({'error': 'Unauthorized access'}), 401


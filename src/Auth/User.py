from flask_login import LoginManager, UserMixin
from flask import jsonify
from .auth_func import get_db_connection
from.queries import query_user_info
from mysql.connector import Error

login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, id, email, firstName, lastName, role):
        self.id=id
        self.email=email
        self.firstName=firstName
        self.lastName=lastName
        self.role=role

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(uid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_user_info, [uid])
        user_info = cursor.fetchone()
        conn.commit()
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "databse error",
            "error": e
        })
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
    if user_info:
        return User(
            uid=user_info['uid'],
            email=user_info['email'],
            firstName=user_info['first_name'],
            lastName=user_info['last_name'],
            role=user_info['name']
        )
    else:
        return
    
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized access'}), 401


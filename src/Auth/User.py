# src/Auth/User.py
from flask_login import LoginManager, UserMixin
from .auth_func import get_db_connection
from .queries import query_user_info
from mysql.connector import Error

login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, id: str, email: str, firstName: str, lastName: str, role: str):
        self.id = str(id)
        self.email = email
        self.firstName = firstName
        self.lastName = lastName
        self.role = role

    def get_id(self) -> str:
        return self.id


@login_manager.user_loader
def load_user(uid: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_user_info, [uid])
        user_info = cursor.fetchone()

    except Error as e:
        print("user_loader DB error:", e)
        return None

    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass

    if not user_info:
        return None

    return User(
        id=user_info["uid"],
        email=user_info["email"],
        firstName=user_info["first_name"],
        lastName=user_info["last_name"],
        role=user_info.get("role") or user_info.get("name", "customer")
    )


@login_manager.unauthorized_handler
def unauthorized():
    return ("Unauthorized", 401)

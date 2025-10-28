from flask import Blueprint, request, jsonify
from flask_login import login_required
from .admin_func import *

verifysalon = Blueprint("verifysalon",__name__,url_prefix='admin')

@verifysalon.route('/approve-salon')
@login_required
def verify_salon():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE business JOIN users ON business.uid=users.uid SET status=TRUE WHERE users.uid=%s",[data['uid']])
    except Error as e:
        return 
    
    
    
    
    
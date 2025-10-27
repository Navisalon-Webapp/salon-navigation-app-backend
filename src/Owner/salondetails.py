from flask import Blueprint, request, jsonify
from mysql.connector import Error
from flask_login import login_required, current_user
from .owner_func import *

salondetails = Blueprint("salondetails", __name__, url_prefix='/owner')

@salondetails.route('/salondetails',methods=["POST"])
def get_salonDetails():
    data = request.get_json()
    if data:
        uid = data['uid']
    elif current_user.is_authenticated:
        uid = current_user.id
    
    if uid:
        return get_business_info(uid)

    
@salondetails.route('/manage-details', methods=['POST'])
@login_required
def manage_details():
    data = request.get_json()
    try:
        update_salon(data)
        return jsonify({
            "status": "success",
            "message": "updated salon details"
        })
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "database error",
            "error": e
        })

        
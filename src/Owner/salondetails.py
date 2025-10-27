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
    """
    Send all salon details through api request including old and new values
    Expecting uid firstName lastName phoneNumber salonName salonStreet salonCity salonState salonCountry salonZipCode
    """
    data = request.get_json()

    if len(data) < 10:
        return jsonify({
            "status":"failure",
            "message":"Not enough values sent through api request"
        })
    
    # expecting the following keys in data variable
    for key in data:
        if(key == "uid"):
            continue
        elif(key == "firstName"):
            continue
        elif(key == "lastName"):
            continue
        elif(key == "phoneNumber"):
            continue
        elif(key == "salonName"):
            continue
        elif(key == "salonStreet"):
            continue
        elif(key == "salonCity"):
            continue
        elif(key == "salonState"):
            continue
        elif(key == "salonCountry"):
            continue
        elif(key == "salonZipCode"):
            continue
        else:
            return

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

        
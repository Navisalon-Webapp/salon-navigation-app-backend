from flask import Blueprint, request, jsonify
from mysql.connector import Error
from flask_login import login_required, current_user
from .owner_func import *

salondetails = Blueprint("salondetails", __name__, url_prefix='/owner')

@salondetails.route('/salon', methods=['GET'])
@login_required
def get_salon():
    try:
        uid = current_user.id
        salon = get_salon_details_by_uid(uid)
        
        if not salon:
            return jsonify({
                "status": "failure",
                "message": "Salon not found"
            }), 404
        
        return jsonify({
            "bid": salon["bid"],
            "name": salon["name"],
            "status": bool(salon["status"]),
            "street": salon.get("street"),
            "city": salon.get("city"),
            "state": salon.get("state"),
            "zip_code": salon.get("zip_code"),
            "year_est": salon.get("year_est")
        }), 200
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500


@salondetails.route('/manage-details', methods=['PUT'])
@login_required
def manage_details():
    try:
        uid = current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "failure",
                "message": "No data provided"
            }), 400
        
        name = data.get("name")
        status = data.get("status", False)
        street = data.get("street", "")
        city = data.get("city", "")
        state = data.get("state", "")
        zip_code = data.get("zip_code", "")
        year_est = data.get("year_est", "")
        
        if not name:
            return jsonify({
                "status": "failure",
                "message": "Salon name is required"
            }), 400
        
        update_salon_details_by_uid(uid, name, status, street, city, state, zip_code, year_est)
        
        return jsonify({
            "status": "success",
            "message": "Salon details updated successfully"
        }), 200
    except Error as e:
        return jsonify({
            "status": "failure",
            "message": "Database error",
            "error": str(e)
        }), 500

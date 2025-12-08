from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *
from .queries import *
import re
import base64

profile = Blueprint("profile", __name__, url_prefix='/employee')

@profile.route('/profile/<eid>', methods=['GET'])
def get_employee_profile(eid):
    if not eid:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query_employee_info, [eid])
            info = cursor.fetchone()
            if not info:
                print("Employee not found")
                return jsonify({
                    "status": "failure",
                    "message": "employee not found"
                }), 404

            profile_picture = info.get('profile_picture')
            if profile_picture:
                if isinstance(profile_picture, bytes):
                    info['profile_picture'] = f"data:image/jpeg;base64,{profile_picture.decode('utf-8')}"
                else:
                    info['profile_picture'] = f"data:image/jpeg;base64,{profile_picture}"
        except mysql.connector.Error as e:
            print(f"Database Error {e}")
            return jsonify({
                "status":"failure",
                "message":"Database Error fetching employee info",
                "error": str(e)
            }), 500
        except Exception as e:
            print(f"Error {e}")
            return jsonify({
                "status":"failure",
                "message":"Error fetching employee info",
                "error": str(e)
            }), 500
        try:
            cursor.execute(query_employee_expertise, [eid])
            expertise = cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Database Error {e}")
            return jsonify({
                "status":"failure",
                "message":"Database Error fetching expertise",
                "error": str(e)
            }), 500
        except Exception as e:
            print(f"Error {e}")
            return jsonify({
                "status":"failure",
                "message":"Error fetching expertise",
                "error": str(e)
            }), 500
        return jsonify({
            "status":"success",
            "message":"retrieved employee profile",
            "employee name":[info['first_name'], info['last_name']],
            "business": [info['bid'], info['name']],
            "bio":info['bio'],
            "contact info":[info['email'], info['phone']],
            "expertise": expertise,
            "approved": info['approved'],
            "profile picture": info['profile_picture']
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/pictures/<eid>', methods=['GET'])
def get_employee_pictures(eid):
    if not eid:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_employee_images, [eid])
        images = cursor.fetchall()

        for image in images:
            if image['picture']:
                if isinstance(image['picture'], bytes):
                    image['picture'] = f"data:image/jpeg;base64,{image['picture'].decode('utf-8')}"
                else:
                    image['picture'] = f"data:image/jpeg;base64,{image['picture']}"
                    
        return jsonify(images), 200

    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/reviews/<eid>', methods=['GET'])
def get_employee_reviews(eid):
    if not eid:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_employee_reviews, [eid])
        reviews = cursor.fetchall()
        return jsonify(reviews), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/stats/<eid>', methods=['GET'])
def get_employee_statistics(eid):
    if not eid:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_total_appointments, [eid])
        appt_count = cursor.fetchone()
        cursor.execute(query_average_rating, [eid])
        avg_rating = cursor.fetchone()
        return jsonify({
            "status":"success",
            "message":"retrieved employee total appointments and average rating",
            "total appointments": appt_count['total_appointments'],
            "average rating": avg_rating['average_rating']
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
@profile.route('/bio/update', methods=['PATCH'])
@login_required
def update_bio():
    eid = get_curr_eid()
    if(check_role() != 'employee' or not eid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    data = request.get_json()
    bio = data['bio'] if data['bio'] else None
    if not bio:
        print("missing parameters")
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        }), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_employee_bio, [bio, eid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"updated employee bio",
            "employee id": eid
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/name/update', methods=['PATCH'])
@login_required
def update_name():
    """
    update name of employee

    send single string of first and last name separated by a space
    """
    eid = get_curr_eid()
    if(check_role() != 'employee' or not eid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    data = request.get_json()
    name = data['name'] if data['name'] else None
    if not name:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400
    
    nameList = name.split(" ", 1)
    if len(nameList) < 2:
        print("Must provide first and last name seperated by space")
        return jsonify({
            "status":"failure",
            "message":"provide first and last name seperated by space"
        }), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_employee_name, [nameList[0], nameList[1], eid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"updated employee name",
            "employee id":eid
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/business/update', methods=['PATCH'])
@login_required
def update_business():
    """
    Update business where employee works
    
    approved status will be reset upon update
    """
    eid = get_curr_eid()
    if(check_role() != 'employee' or not eid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    data = request.get_json()
    bid = data['bid'] if data['bid'] else None
    if not bid:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_employee_business, [bid, eid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"updated employee business",
            "employee id": eid
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/phone/update', methods=['PATCH'])
@login_required
def update_phone():
    """
    Update employee phone number
    """
    eid = get_curr_eid()
    if(check_role() != 'employee' or not eid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    data = request.get_json()
    phone = data['phone'] if data['phone'] else None
    if not phone:
        print("missing parameter")
        return jsonify({
            "status":"failure",
            "message":"missing parameter"
        }), 400
    phone_clean = re.sub(r'[^0-9]', '', phone)
    

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_employee_phone, [phone_clean, eid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"updated employee business",
            "employee id": eid
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/profile-picture/upload', methods=['PATCH'])
@login_required
def upload_profile_image():
    """
    Upload employee profile picture
    """
    eid = get_curr_eid()
    if(check_role() != 'employee' or not eid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    if 'image' not in request.files:
        return jsonify({"message": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    conn = None
    cursor = None
    try:
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        mime_type = file.content_type or 'image/jpeg'
        if not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(update_profile_picture, [image_base64, eid])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"updated employee picture",
            "employee id": eid
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@profile.route('/employee/picture/upload', methods=['POST'])
@login_required
def upload_picture():
    """
    Upload pictures for employee profile page to showcase work
    """
    eid = get_curr_eid()
    if(check_role() != 'employee' or not eid):
        print("Unauthorized")
        return jsonify({
            "status":"failure",
            "message":"user is not an employee",
        }), 401
    
    if 'image' not in request.files:
        return jsonify({"message": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    conn = None
    cursor = None
    try:
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        mime_type = file.content_type or 'image/jpeg'
        if not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_employee_picture, [eid, image_base64])
        conn.commit()
        return jsonify({
            "status":"success",
            "message":"inserted picture",
            "employee id": eid
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




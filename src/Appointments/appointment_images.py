from flask import Blueprint, request, jsonify
from flask_login import login_required
from helper.utils import get_db_connection
import mysql.connector
import base64

appointment_images = Blueprint("appointment_images", __name__, url_prefix="/api")

@appointment_images.route("/appointments/<int:aid>/images", methods=["GET"])
@login_required
def get_appointment_images(aid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT before_image, after_image
            FROM appointments
            WHERE aid = %s
        """, (aid,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({"message": "Appointment not found"}), 404
        
        response = {}
        if result['before_image']:
            # Handle if image is stored as bytes or string
            if isinstance(result['before_image'], bytes):
                response['before_image'] = f"data:image/jpeg;base64,{result['before_image'].decode('utf-8')}"
            else:
                response['before_image'] = f"data:image/jpeg;base64,{result['before_image']}"
        
        if result['after_image']:
            # Handle if image is stored as bytes or string
            if isinstance(result['after_image'], bytes):
                response['after_image'] = f"data:image/jpeg;base64,{result['after_image'].decode('utf-8')}"
            else:
                response['after_image'] = f"data:image/jpeg;base64,{result['after_image']}"
        
        return jsonify(response), 200
        
    except mysql.connector.Error as err:
        if conn:
            conn.close()
        return jsonify({"message": f"Database error: {err}"}), 500

@appointment_images.route("/appointments/<int:aid>/upload-image", methods=["POST"])
@login_required
def upload_appointment_image(aid):
    if 'image' not in request.files:
        return jsonify({"message": "No image file provided"}), 400
    
    file = request.files['image']
    image_type = request.form.get('type')
    
    if not image_type or image_type not in ['before', 'after']:
        return jsonify({"message": "Invalid image type. Must be 'before' or 'after'"}), 400
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
    
    try:
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Detect MIME type from file extension or content type
        mime_type = file.content_type or 'image/jpeg'
        if not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "Database connection error"}), 500
        
        cursor = conn.cursor()
        
        column_name = f"{image_type}_image"
        query = f"UPDATE appointments SET {column_name} = %s WHERE aid = %s"
        cursor.execute(query, (image_base64, aid))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        response = {}
        response[f'{image_type}_image'] = f"data:{mime_type};base64,{image_base64}"
        
        return jsonify(response), 200
        
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"message": f"Database error: {err}"}), 500
    except Exception as e:
        return jsonify({"message": f"Error processing image: {str(e)}"}), 500

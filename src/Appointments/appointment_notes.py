from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from helper.utils import get_db_connection
import mysql.connector
from datetime import datetime

appointment_notes = Blueprint("appointment_notes", __name__, url_prefix="/api")

@appointment_notes.route("/appointments/<int:aid>/notes", methods=["GET"])
@login_required
def get_appointment_notes(aid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                an.note_id as id,
                an.note_text as text,
                an.created_at as createdAt,
                u.first_name,
                u.last_name,
                CASE 
                    WHEN an.author_role = 'customer' THEN 'Client'
                    WHEN an.author_role = 'employee' THEN 'Worker'
                    WHEN an.author_role = 'owner' THEN 'Owner'
                    ELSE 'User'
                END as role
            FROM appointment_notes an
            JOIN users u ON an.author_uid = u.uid
            WHERE an.aid = %s
            ORDER BY an.created_at DESC
        """, (aid,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        notes = []
        for row in rows:
            notes.append({
                "id": str(row['id']),
                "author": f"{row['first_name']} {row['last_name']} ({row['role']})",
                "text": row['text'],
                "createdAt": row['createdAt'].isoformat() if row['createdAt'] else None
            })
        
        return jsonify({"notes": notes}), 200
        
    except mysql.connector.Error as err:
        if conn:
            conn.close()
        return jsonify({"message": f"Database error: {err}"}), 500

@appointment_notes.route("/appointments/<int:aid>/notes", methods=["POST"])
@login_required
def add_appointment_note(aid):
    data = request.get_json()
    note_text = data.get("note")
    
    if not note_text or not note_text.strip():
        return jsonify({"message": "Note text is required"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO appointment_notes (aid, author_uid, author_role, note_text, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (aid, current_user.id, current_user.role, note_text.strip(), datetime.now()))
        
        conn.commit()
        note_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT u.first_name, u.last_name
            FROM users u
            WHERE u.uid = %s
        """, (current_user.id,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        role_label = {
            'customer': 'Client',
            'employee': 'Worker',
            'owner': 'Owner'
        }.get(current_user.role, 'User')
        
        return jsonify({
            "note": {
                "id": str(note_id),
                "author": f"{user['first_name']} {user['last_name']} ({role_label})",
                "text": note_text.strip(),
                "createdAt": datetime.now().isoformat()
            }
        }), 201
        
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"message": f"Database error: {err}"}), 500

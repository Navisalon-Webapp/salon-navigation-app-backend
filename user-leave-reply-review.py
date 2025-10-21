from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()



app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()
#users can leave reviews
@app.route("/api/user/leave-reply-review", methods=["POST"])
def leave_reply():
    data = request.get_json()
    user_id = data.get("uid")
    business_id = data.get("bid")
    employee_id = data.get("eid")
    parent_id = data.get("parent_id")  
    comments = data.get("comments")
    query = """ 
    insert into reviews(uid,bid,eid,parent_id,comments)
    values(%s, %s, %s, %s, %s);
 """
    cursor.execute(query, (user_id,business_id,employee_id, parent_id, comments))
    db.commit()
    return jsonify({"message": "Reply submitted successfully."}), 201




if __name__ == "__main__":
    app.run(debug=True)

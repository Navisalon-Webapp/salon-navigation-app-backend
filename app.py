from flask import Flask
import mysql.connector
from flask_cors import CORS
from src.Auth.signup import signup

app = Flask(__name__)
CORS(app)
app.register_blueprint(signup)

@app.route('/')       
def hello(): 
    return 'HELLO'
  
if __name__=='__main__': 
   app.run(debug=True)
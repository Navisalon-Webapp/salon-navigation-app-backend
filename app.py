from flask import Flask
import os
from dotenv import load_dotenv 
from flask_cors import CORS
from src.Auth.signup import signup
from src.Auth.signin import signin

load_dotenv()

app = Flask(__name__)
CORS(app)
app.register_blueprint(signup)
app.register_blueprint(signin)

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')

@app.route('/')       
def hello(): 
    return 'HELLO'
  
if __name__=='__main__': 
   app.run(debug=True)
from flask import Flask
from routes.signup import signup

app = Flask(__name__)
app.register_blueprint(signup)

@app.route('/')       
def hello(): 
    return 'HELLO'
  
if __name__=='__main__': 
   app.run(debug=True)
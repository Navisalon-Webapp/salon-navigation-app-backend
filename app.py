from flask import Flask
import os
from dotenv import load_dotenv
from flask_cors import CORS
from src.Auth.signup import signup
from src.Auth.signin import signin
from src.Auth import init_auth
from src.Clients.Clients_Browse import client_browse

load_dotenv()

app = Flask(__name__)
CORS(app)
app.register_blueprint(signup)
app.register_blueprint(signin)
app.register_blueprint(client_browse)

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')

init_auth(app)



if __name__ == "__main__":
    app.run(debug=True)
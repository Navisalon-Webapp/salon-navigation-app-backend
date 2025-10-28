from flask import Flask
import os
from dotenv import load_dotenv
from flask_cors import CORS
from src.Auth.signup import signup
from src.Auth.signin import signin
from src.Worker.appointments import appointments
from src.Owner.salondetails import salondetails
from src.Auth import init_auth
from src.Clients.Clients_Browse import client_browse
from src.Worker.Workers_Browse import workers_browse
from src.Reviews.Post_Reviews import post_reviews
from src.Appointments.clients_cancel_appt import cancel_appts
from src.Appointments.users_add_appt_notes import add_notes
from src.Email_Subscriptions.clients_mnge_email_subs import manage_email_sub
from src.Auth.User import login_manager
from src.Appointments.schedule_appt import schedule_appt
from src.Worker.manage_availability import worker_avail
from src.Salon.manage_services import manage_services

load_dotenv()

app = Flask(__name__)

app.secret_key = "dev-change-me"
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = "signin.getSignin"

CORS(
    app,
    supports_credentials=True,
    resources={r"/*": {"origins": ["http://localhost:5173"]}}
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

app.register_blueprint(signup)
app.register_blueprint(signin)
app.register_blueprint(appointments)
app.register_blueprint(salondetails)
app.register_blueprint(client_browse)
app.register_blueprint(workers_browse)
app.register_blueprint(post_reviews)
app.register_blueprint(cancel_appts)
app.register_blueprint(add_notes)
app.register_blueprint(manage_email_sub)
app.register_blueprint(schedule_appt)
app.register_blueprint(worker_avail)
app.register_blueprint(manage_services)

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')

init_auth(app)



if __name__ == "__main__":
    app.run(debug=True)
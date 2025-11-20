from flask import Flask
import os
from dotenv import load_dotenv
from flask_cors import CORS
import atexit
from src.extensions import mail
from src.Auth.signup import signup
from src.Auth.signin import signin
from src.Worker.appointments import appointments
from src.Owner.salondetails import salondetails
from src.Owner.manage_products import manage_products
from src.Clients.Clients_Browse.Clients_Browse import client_browse
from src.Worker.Workers_Browse import workers_browse
from src.Reviews.Post_Reviews import post_reviews
from src.Appointments.clients_cancel_appt import cancel_appts
from src.Appointments.users_add_appt_notes import add_notes
from src.Email_Subscriptions.clients_mnge_email_subs import manage_email_sub
from src.Auth.User import login_manager
from src.Appointments.schedule_appt import schedule_appt
from src.Appointments.get_available_workers import get_avail_workers
from src.Appointments.get_worker_slots import get_worker_slots
from src.Appointments.appointment_images import appointment_images
from src.Appointments.appointment_notes import appointment_notes
from src.Worker.manage_availability import worker_avail
from src.Salon.manage_services import manage_services
from src.Salon.approve_workers import approve_workers
from src.Notifications.notifications import notification
from src.Admin.verifysalon import verifysalon
from src.LoyaltyProgram.create_loyalty_programs import loyalty_prog
from src.Promotions.create_promos import promotions
from src.Clients.Clients_Review.Clients_Review_Workers import review_workers
from src.ViewVisitHistory.owner_view_visit_history import visit_hist
from src.Admin.metrics import metrics
from src.Admin.Uptime.uptime import uptime
from src.Clients.Clients_Manage_Cart.clients_addto_cart import addto_cart
from src.Clients.Clients_Manage_Cart.clients_view_cart import manage_cart
from src.Clients.View_Loyal_Points.view_loyalty_points import view_lpoints
from src.Admin.Uptime.service import Service
from src.Revenue.get_revenue import revenue
from src.Clients.get_appointment import get_appointment
from src.Clients.appointment_deposit import deposit




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
 
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_SUPPRESS_SEND'] = False

mail.init_app(app)

app.register_blueprint(signup)
app.register_blueprint(signin)
app.register_blueprint(appointments)
app.register_blueprint(salondetails)
app.register_blueprint(manage_products)
app.register_blueprint(client_browse)
app.register_blueprint(workers_browse)
app.register_blueprint(post_reviews)
app.register_blueprint(cancel_appts)
app.register_blueprint(add_notes)
app.register_blueprint(manage_email_sub)
app.register_blueprint(schedule_appt)
app.register_blueprint(get_avail_workers)
app.register_blueprint(get_worker_slots)
app.register_blueprint(appointment_images)
app.register_blueprint(appointment_notes)
app.register_blueprint(worker_avail)
app.register_blueprint(manage_services)
app.register_blueprint(approve_workers)
app.register_blueprint(notification)
app.register_blueprint(verifysalon)
app.register_blueprint(loyalty_prog)
app.register_blueprint(promotions)
app.register_blueprint(review_workers)
app.register_blueprint(visit_hist)
app.register_blueprint(metrics)
app.register_blueprint(addto_cart)
app.register_blueprint(manage_cart)
app.register_blueprint(view_lpoints)
app.register_blueprint(uptime)
app.register_blueprint(revenue)
app.register_blueprint(get_appointment)
app.register_blueprint(deposit)

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')

service = Service()

atexit.register(service.stop_monitoring)


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from src.extensions import scheduler
        with app.app_context():
            if not scheduler.running:
                scheduler.start()
                print("Scheduler started successfully")
            service.start()
    app.run(debug=True, use_reloader=False)
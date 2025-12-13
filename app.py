from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
# import atexit
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
from src.LoyaltyProgram.loyalty_points import loyalty_points
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
from src.Clients.payment import payment
from src.Clients.transactions import transaction
from src.Owner.operation_time import operation
from src.Clients.save_favorites import saved_favorites
from src.Worker.profile import profile
from src.Salon.deposit import deposit_rate
from src.Salon.appointments import business_appointments
from src.Admin.verifyadmin import verifyadmin



load_dotenv()

app = Flask(__name__)

SWAGGER_URL = "/docs"
API_SPEC_URL = "/swagger.json"

ADDITIONAL_ENDPOINT_DETAILS = {
    "signin.getSignin": {
        "post": {
            "consumes": ["application/json"],
            "parameters": [
                {
                    "in": "body",
                    "name": "credentials",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                            },
                            "password": {
                                "type": "string",
                            },
                        },
                    },
                }
            ],
            "responses": {
                "200": {
                    "description": "Signed in successfully.",
                },
                "400": {
                    "description": "Missing credentials or validation error.",
                },
                "401": {
                    "description": "Authentication failed.",
                },
            },
        }
    },
    "signin.reset_password_email": {
        "post": {
            "consumes": ["application/json"],
            "parameters": [
                {
                    "in": "body",
                    "name": "request",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "required": ["email"],
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                            },
                        },
                    },
                }
            ],
        }
    },
    "signin.reset_password": {
        "post": {
            "consumes": ["application/json"],
            "parameters": [
                {
                    "in": "body",
                    "name": "request",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "required": ["uid", "password", "confirmPassword"],
                        "properties": {
                            "uid": {"type": "string"},
                            "password": {"type": "string"},
                            "confirmPassword": {"type": "string"},
                        },
                    },
                }
            ],
        }
    },
}


def generate_swagger_spec(flask_app: Flask) -> dict:
    paths = {}
    tag_set = set()

    for rule in flask_app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        if rule.rule == API_SPEC_URL or rule.rule.startswith(SWAGGER_URL):
            continue

        available_methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        if not available_methods:
            continue

        endpoint_name = rule.endpoint
        tag_name = endpoint_name.split(".")[0] if "." in endpoint_name else "default"
        tag_set.add(tag_name)

        methods = {}
        for method in available_methods:
            method_name = method.lower()
            method_spec = {
                "tags": [tag_name],
                "summary": endpoint_name,
                "responses": {
                    "200": {"description": "Success"},
                },
            }

            overrides = ADDITIONAL_ENDPOINT_DETAILS.get(endpoint_name, {}).get(method_name)
            if overrides:
                merged = dict(method_spec)
                merged.update({k: v for k, v in overrides.items() if k != "parameters"})
                if "parameters" in overrides:
                    merged["parameters"] = overrides["parameters"]
                method_spec = merged

            methods[method_name] = method_spec

        paths[str(rule.rule)] = methods

    return {
        "swagger": "2.0",
        "info": {
            "title": "Salon Navigation API",
            "description": "Automatically generated documentation for the Salon Navigation backend.",
            "version": "1.0.0",
        },
        "basePath": "/",
        "tags": [{"name": tag} for tag in sorted(tag_set)],
        "paths": paths,
    }

app.secret_key = "dev-change-me"
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = "signin.getSignin"

CORS(
    app,
    supports_credentials=True,
    resources={r"/*": {"origins": "*"}}
)

# Detect if running in production (on Render)
is_production = os.getenv("RENDER") is not None or os.getenv("PRODUCTION") == "true"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None" if is_production else "Lax",
    SESSION_COOKIE_SECURE=True if is_production else False,
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
app.register_blueprint(loyalty_points)
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
app.register_blueprint(payment)
app.register_blueprint(transaction)
app.register_blueprint(operation)
app.register_blueprint(saved_favorites)
app.register_blueprint(profile)
app.register_blueprint(deposit_rate)
app.register_blueprint(business_appointments)
app.register_blueprint(verifyadmin)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_SPEC_URL,
    config={"app_name": "Salon Navigation API"},
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route(API_SPEC_URL)
def swagger_spec():
    return jsonify(generate_swagger_spec(app))

app.config['SECRET_KEY']=os.getenv('SECRET_KEY')

# service = Service()

# atexit.register(service.stop_monitoring)


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from src.extensions import scheduler
        with app.app_context():
            if not scheduler.running:
                scheduler.start()
                print("Scheduler started successfully")
            # service.start()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
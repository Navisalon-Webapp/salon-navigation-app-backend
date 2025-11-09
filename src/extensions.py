from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

mail = Mail()
scheduler = BackgroundScheduler()
from flask import Blueprint, request, jsonify
from src.Notifications.notification_func import *
from helper.utils import *
from src.extensions import mail
from flask_mail import Message
from dotenv import load_dotenv
from src.extensions import scheduler
import os

load_dotenv()

notification = Blueprint("notification",__name__,url_prefix='/notification')

@notification.route('/get-jobs', methods=['GET'])
def get_jobs():
    print(scheduler.get_jobs())
    return jsonify("hello")

@notification.route('/test_email',methods=['POST'])
def email_appointment():
    msg = Message('Hello', sender =os.getenv('MAIL_USERNAME'), recipients = [os.getenv('MAIL_USERNAME')] )
    msg.body = 'Hello Flask message sent from Flask-Mail'
    mail.send(msg)
    return jsonify('sent')
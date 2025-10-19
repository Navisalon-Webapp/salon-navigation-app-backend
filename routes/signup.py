from flask import Blueprint, request
signup = Blueprint("signup",__name__, url_prefix='')

@signup.route('client/signup', methods=['POST'])
def getClientSignUp():
    data=request.get_json()

@signup.route('owner/signup', methods=['POST'])
def getOwnerSignUp():
    data=request.get_json()

@signup.route('worker/signup', methods=['POST'])
def getWorkerSignUp():
    data=request.get_json()
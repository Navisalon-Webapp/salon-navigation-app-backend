from flask import Blueprint, request, jsonify

verifysalon = Blueprint("verifysalon",__name__,url_prefix='admin')

@verifysalon.route('/approv-esalon')
def verify_salon():
    data = request.get_json()

    
    
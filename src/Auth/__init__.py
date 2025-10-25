from .User import login_manager

def init_auth(app):
    """Initialize authentication with the Flask app"""
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    login_manager.login_view = 'auth.login'
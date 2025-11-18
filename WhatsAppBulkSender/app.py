import os
from flask import Flask, render_template, redirect, url_for, session
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Import routes
from auth import auth_bp
from admin_routes import admin_bp
from user_routes import user_bp
from message_routes import message_bp
from webhook_routes import webhook_bp
from report_routes import report_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(message_bp, url_prefix='/messages')
app.register_blueprint(webhook_bp, url_prefix='/webhooks')
app.register_blueprint(report_bp, url_prefix='/reports')


@app.route('/')
def index():
    """Redirect to appropriate dashboard based on user role"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))


@app.context_processor
def utility_processor():
    """Make utility functions available in templates"""
    from datetime import datetime
    
    def get_greeting():
        hour = datetime.now().hour
        if hour < 12:
            return "Good Morning"
        elif hour < 18:
            return "Good Afternoon"
        else:
            return "Good Evening"
    
    return dict(get_greeting=get_greeting)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

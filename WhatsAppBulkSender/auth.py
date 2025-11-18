from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from firebase_utils import query_documents, USERS_COLLECTION
from functools import wraps

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        # Query user by email and role
        users = query_documents(USERS_COLLECTION, 'email', '==', email)
        
        if not users:
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        user = users[0]
        
        # Verify role
        if user.get('role') != role:
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        # Verify password
        if not check_password_hash(user.get('password_hash', ''), password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        # Set session
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['name'] = user['name']
        session['role'] = user['role']
        
        # Redirect based on role
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Query user
    users = query_documents(USERS_COLLECTION, 'email', '==', email)
    
    if not users or users[0].get('role') != role:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    user = users[0]
    
    if not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Set session
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['name'] = user['name']
    session['role'] = user['role']
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
    })


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for logout"""
    session.clear()
    return jsonify({'success': True})

from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash
from auth import admin_required
from firebase_utils import (
    create_document, get_document, update_document, delete_document,
    get_all_documents, query_documents, create_audit_log,
    USERS_COLLECTION, BUSINESSES_COLLECTION, TASKS_COLLECTION
)
from cryptography.fernet import Fernet
from config import Config
from datetime import datetime
import base64

admin_bp = Blueprint('admin', __name__)

# Encryption key for business tokens - MUST be set in environment
if not Config.ENCRYPTION_KEY:
    raise ValueError(
        "ENCRYPTION_KEY environment variable is required. "
        "Generate one using: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

cipher_suite = Fernet(Config.ENCRYPTION_KEY.encode() if isinstance(Config.ENCRYPTION_KEY, str) else Config.ENCRYPTION_KEY)


def encrypt_token(token):
    """Encrypt business token"""
    return cipher_suite.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token):
    """Decrypt business token"""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html')


# ============= BUSINESSES CRUD =============

@admin_bp.route('/api/businesses', methods=['GET'])
@admin_required
def get_businesses():
    """Get all businesses"""
    businesses = get_all_documents(BUSINESSES_COLLECTION, order_by='created_at')
    
    # Decrypt tokens for display (or mask them)
    for business in businesses:
        business['business_token'] = '***ENCRYPTED***'
    
    return jsonify({'businesses': businesses})


@admin_bp.route('/api/businesses/<business_id>', methods=['GET'])
@admin_required
def get_business(business_id):
    """Get a specific business"""
    business = get_document(BUSINESSES_COLLECTION, business_id)
    
    if not business:
        return jsonify({'error': 'Business not found'}), 404
    
    business['business_token'] = '***ENCRYPTED***'
    return jsonify({'business': business})


@admin_bp.route('/api/businesses', methods=['POST'])
@admin_required
def create_business():
    """Create a new business"""
    data = request.get_json()
    
    business_name = data.get('business_name')
    business_token = data.get('business_token')
    phone_id = data.get('phone_id')
    waba_id = data.get('waba_id')
    status = data.get('status', 'active')
    
    if not all([business_name, business_token, phone_id, waba_id]):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Encrypt the business token
    encrypted_token = encrypt_token(business_token)
    
    business_data = {
        'business_name': business_name,
        'business_token': encrypted_token,
        'phone_id': phone_id,
        'waba_id': waba_id,
        'status': status,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    business_id = create_document(BUSINESSES_COLLECTION, business_data)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'create',
        'business',
        business_id,
        {'business_name': business_name}
    )
    
    return jsonify({'success': True, 'business_id': business_id}), 201


@admin_bp.route('/api/businesses/<business_id>', methods=['PUT'])
@admin_required
def update_business(business_id):
    """Update a business"""
    data = request.get_json()
    
    business = get_document(BUSINESSES_COLLECTION, business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404
    
    update_data = {
        'updated_at': datetime.utcnow().isoformat()
    }
    
    if 'business_name' in data:
        update_data['business_name'] = data['business_name']
    
    if 'business_token' in data and data['business_token'] != '***ENCRYPTED***':
        update_data['business_token'] = encrypt_token(data['business_token'])
    
    if 'phone_id' in data:
        update_data['phone_id'] = data['phone_id']
    
    if 'waba_id' in data:
        update_data['waba_id'] = data['waba_id']
    
    if 'status' in data:
        update_data['status'] = data['status']
    
    update_document(BUSINESSES_COLLECTION, business_id, update_data)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'update',
        'business',
        business_id,
        update_data
    )
    
    return jsonify({'success': True})


@admin_bp.route('/api/businesses/<business_id>', methods=['DELETE'])
@admin_required
def delete_business(business_id):
    """Delete a business"""
    business = get_document(BUSINESSES_COLLECTION, business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404
    
    delete_document(BUSINESSES_COLLECTION, business_id)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'delete',
        'business',
        business_id,
        {'business_name': business.get('business_name')}
    )
    
    return jsonify({'success': True})


# ============= USERS CRUD =============

@admin_bp.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users"""
    users = get_all_documents(USERS_COLLECTION, order_by='created_at')
    
    # Remove password hashes from response
    for user in users:
        user.pop('password_hash', None)
    
    return jsonify({'users': users})


@admin_bp.route('/api/users/<user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get a specific user"""
    user = get_document(USERS_COLLECTION, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.pop('password_hash', None)
    return jsonify({'user': user})


@admin_bp.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not all([name, email, password]):
        return jsonify({'error': 'Name, email, and password are required'}), 400
    
    # Check if email already exists
    existing_users = query_documents(USERS_COLLECTION, 'email', '==', email)
    if existing_users:
        return jsonify({'error': 'Email already exists'}), 400
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    user_data = {
        'name': name,
        'email': email,
        'password_hash': password_hash,
        'role': role,
        'created_by_admin_id': session['user_id'],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    user_id = create_document(USERS_COLLECTION, user_data)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'create',
        'user',
        user_id,
        {'name': name, 'email': email, 'role': role}
    )
    
    return jsonify({'success': True, 'user_id': user_id}), 201


@admin_bp.route('/api/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update a user"""
    data = request.get_json()
    
    user = get_document(USERS_COLLECTION, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    update_data = {
        'updated_at': datetime.utcnow().isoformat()
    }
    
    if 'name' in data:
        update_data['name'] = data['name']
    
    if 'email' in data and data['email'] != user.get('email'):
        # Check if new email already exists
        existing_users = query_documents(USERS_COLLECTION, 'email', '==', data['email'])
        if existing_users:
            return jsonify({'error': 'Email already exists'}), 400
        update_data['email'] = data['email']
    
    if 'password' in data and data['password']:
        update_data['password_hash'] = generate_password_hash(data['password'])
    
    if 'role' in data:
        update_data['role'] = data['role']
    
    update_document(USERS_COLLECTION, user_id, update_data)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'update',
        'user',
        user_id,
        {k: v for k, v in update_data.items() if k != 'password_hash'}
    )
    
    return jsonify({'success': True})


@admin_bp.route('/api/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = get_document(USERS_COLLECTION, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    delete_document(USERS_COLLECTION, user_id)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'delete',
        'user',
        user_id,
        {'name': user.get('name'), 'email': user.get('email')}
    )
    
    return jsonify({'success': True})


# ============= TASKS CRUD =============

@admin_bp.route('/api/tasks', methods=['GET'])
@admin_required
def get_tasks():
    """Get all tasks"""
    tasks = get_all_documents(TASKS_COLLECTION, order_by='created_at')
    return jsonify({'tasks': tasks})


@admin_bp.route('/api/tasks/<task_id>', methods=['GET'])
@admin_required
def get_task(task_id):
    """Get a specific task"""
    task = get_document(TASKS_COLLECTION, task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({'task': task})


@admin_bp.route('/api/tasks', methods=['POST'])
@admin_required
def create_task():
    """Create a new task"""
    data = request.get_json()
    
    title = data.get('title')
    assigned_user_id = data.get('assigned_user_id')
    business_id = data.get('business_id')
    description = data.get('description', '')
    status = data.get('status', 'pending')
    
    if not all([title, assigned_user_id, business_id]):
        return jsonify({'error': 'Title, assigned_user_id, and business_id are required'}), 400
    
    # Verify user exists
    user = get_document(USERS_COLLECTION, assigned_user_id)
    if not user:
        return jsonify({'error': 'Assigned user not found'}), 404
    
    # Verify business exists
    business = get_document(BUSINESSES_COLLECTION, business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404
    
    task_data = {
        'title': title,
        'assigned_user_id': assigned_user_id,
        'business_id': business_id,
        'description': description,
        'status': status,
        'created_by': session['user_id'],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    task_id = create_document(TASKS_COLLECTION, task_data)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'create',
        'task',
        task_id,
        {'title': title, 'assigned_user_id': assigned_user_id}
    )
    
    return jsonify({'success': True, 'task_id': task_id}), 201


@admin_bp.route('/api/tasks/<task_id>', methods=['PUT'])
@admin_required
def update_task(task_id):
    """Update a task"""
    data = request.get_json()
    
    task = get_document(TASKS_COLLECTION, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    update_data = {
        'updated_at': datetime.utcnow().isoformat()
    }
    
    if 'title' in data:
        update_data['title'] = data['title']
    
    if 'description' in data:
        update_data['description'] = data['description']
    
    if 'status' in data:
        update_data['status'] = data['status']
    
    if 'assigned_user_id' in data:
        user = get_document(USERS_COLLECTION, data['assigned_user_id'])
        if not user:
            return jsonify({'error': 'Assigned user not found'}), 404
        update_data['assigned_user_id'] = data['assigned_user_id']
    
    if 'business_id' in data:
        business = get_document(BUSINESSES_COLLECTION, data['business_id'])
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        update_data['business_id'] = data['business_id']
    
    update_document(TASKS_COLLECTION, task_id, update_data)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'update',
        'task',
        task_id,
        update_data
    )
    
    return jsonify({'success': True})


@admin_bp.route('/api/tasks/<task_id>', methods=['DELETE'])
@admin_required
def delete_task(task_id):
    """Delete a task"""
    task = get_document(TASKS_COLLECTION, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    delete_document(TASKS_COLLECTION, task_id)
    
    # Create audit log
    create_audit_log(
        session['user_id'],
        'delete',
        'task',
        task_id,
        {'title': task.get('title')}
    )
    
    return jsonify({'success': True})


# ============= UI ROUTES =============

@admin_bp.route('/businesses')
@admin_required
def businesses_page():
    """Businesses management page"""
    return render_template('admin/businesses.html')


@admin_bp.route('/users')
@admin_required
def users_page():
    """Users management page"""
    return render_template('admin/users.html')


@admin_bp.route('/tasks')
@admin_required
def tasks_page():
    """Tasks management page"""
    return render_template('admin/tasks.html')

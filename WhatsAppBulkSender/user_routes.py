from flask import Blueprint, render_template, request, jsonify, session
from auth import login_required
from firebase_utils import (
    get_document, update_document, query_documents, get_all_documents,
    TASKS_COLLECTION, MESSAGES_COLLECTION
)
from datetime import datetime

user_bp = Blueprint('user', __name__)


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template('user/dashboard.html')


@user_bp.route('/api/tasks/assigned', methods=['GET'])
@login_required
def get_assigned_tasks():
    """Get tasks assigned to the logged-in user"""
    tasks = query_documents(TASKS_COLLECTION, 'assigned_user_id', '==', session['user_id'])
    
    # Sort by created_at (most recent first)
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({'tasks': tasks})


@user_bp.route('/api/tasks/<task_id>/status', methods=['PUT'])
@login_required
def update_task_status(task_id):
    """Update task status"""
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({'error': 'Status is required'}), 400
    
    # Verify task belongs to user
    task = get_document(TASKS_COLLECTION, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if task.get('assigned_user_id') != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    update_data = {
        'status': status,
        'updated_at': datetime.utcnow().isoformat()
    }
    
    update_document(TASKS_COLLECTION, task_id, update_data)
    
    return jsonify({'success': True})


@user_bp.route('/api/messages/history', methods=['GET'])
@login_required
def get_message_history():
    """Get message history for the logged-in user"""
    messages = query_documents(MESSAGES_COLLECTION, 'user_id', '==', session['user_id'])
    
    # Sort by created_at (most recent first)
    messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({'messages': messages})


@user_bp.route('/send-message')
@login_required
def send_message_page():
    """Send message page"""
    return render_template('user/send_message.html')


@user_bp.route('/history')
@login_required
def history_page():
    """Message history page"""
    return render_template('user/history.html')

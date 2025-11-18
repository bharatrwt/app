from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
import phonenumbers
from auth import login_required
from firebase_utils import (
    create_document, get_document, update_document, query_documents,
    MESSAGES_COLLECTION, MESSAGE_RECIPIENTS_COLLECTION, TASKS_COLLECTION,
    BUSINESSES_COLLECTION
)
from config import Config
from datetime import datetime
import uuid

message_bp = Blueprint('messages', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def parse_csv_file(file_path):
    """Parse CSV/Excel file and extract phone numbers"""
    try:
        # Determine file type and read
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:  # xlsx
            df = pd.read_excel(file_path)
        
        # Find column with phone numbers (first column or column named 'phone', 'number', etc.)
        phone_column = None
        for col in df.columns:
            if 'phone' in col.lower() or 'number' in col.lower() or 'mobile' in col.lower():
                phone_column = col
                break
        
        if phone_column is None:
            phone_column = df.columns[0]
        
        # Extract and validate phone numbers
        phone_numbers = []
        errors = []
        
        for idx, value in enumerate(df[phone_column]):
            try:
                # Convert to string and remove whitespace
                phone_str = str(value).strip()
                
                # Parse phone number (try to detect country, default to international format)
                parsed_number = phonenumbers.parse(phone_str, None)
                
                # Validate
                if phonenumbers.is_valid_number(parsed_number):
                    # Format to E.164
                    e164_number = phonenumbers.format_number(
                        parsed_number,
                        phonenumbers.PhoneNumberFormat.E164
                    )
                    phone_numbers.append(e164_number)
                else:
                    errors.append(f"Row {idx + 1}: Invalid number - {phone_str}")
            except Exception as e:
                errors.append(f"Row {idx + 1}: Error parsing {phone_str} - {str(e)}")
        
        # Remove duplicates
        unique_numbers = list(set(phone_numbers))
        
        return unique_numbers, errors
    
    except Exception as e:
        raise Exception(f"Error parsing file: {str(e)}")


@message_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    """Send bulk WhatsApp messages"""
    try:
        # Get form data
        task_id = request.form.get('task_id')
        media_url = request.form.get('media_url')
        title = request.form.get('title')
        body = request.form.get('body')
        
        # Validate required fields
        if not all([media_url, title, body]):
            return jsonify({'error': 'Media URL, title, and body are required'}), 400
        
        # Get file
        if 'recipients_file' not in request.files:
            return jsonify({'error': 'Recipients file is required'}), 400
        
        file = request.files['recipients_file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only CSV and XLSX files are allowed'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_filename = f"{uuid.uuid4()}_{filename}"
        temp_path = os.path.join('/tmp', temp_filename)
        file.save(temp_path)
        
        # Parse file
        try:
            phone_numbers, errors = parse_csv_file(temp_path)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        if not phone_numbers:
            return jsonify({
                'error': 'No valid phone numbers found in file',
                'parsing_errors': errors
            }), 400
        
        # Get business_id from task
        business_id = None
        if task_id:
            task = get_document(TASKS_COLLECTION, task_id)
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            
            # Verify task belongs to user
            if task.get('assigned_user_id') != session['user_id']:
                return jsonify({'error': 'Access denied'}), 403
            
            business_id = task.get('business_id')
        
        if not business_id:
            return jsonify({'error': 'Business ID is required'}), 400
        
        # Verify business exists
        business = get_document(BUSINESSES_COLLECTION, business_id)
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        
        if business.get('status') != 'active':
            return jsonify({'error': 'Business is not active'}), 400
        
        # Create message record
        message_data = {
            'task_id': task_id,
            'business_id': business_id,
            'user_id': session['user_id'],
            'media_url': media_url,
            'title': title,
            'body': body,
            'total_recipients': len(phone_numbers),
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
            'stats': {
                'queued': len(phone_numbers),
                'sent': 0,
                'delivered': 0,
                'seen': 0,
                'failed': 0,
                'replied': 0
            }
        }
        
        message_id = create_document(MESSAGES_COLLECTION, message_data)
        
        # Create message recipient records
        recipient_ids = []
        for phone_number in phone_numbers:
            recipient_data = {
                'message_id': message_id,
                'phone_number': phone_number,
                'status': 'queued',
                'meta': {},
                'reply_text': None,
                'delivered_at': None,
                'seen_at': None,
                'reply_at': None,
                'created_at': datetime.utcnow().isoformat()
            }
            recipient_id = create_document(MESSAGE_RECIPIENTS_COLLECTION, recipient_data)
            recipient_ids.append(recipient_id)
        
        # Queue message for processing
        from worker import queue_message_job
        queue_message_job(message_id, business_id, recipient_ids)
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'total_recipients': len(phone_numbers),
            'queued_count': len(phone_numbers),
            'parsing_errors': errors if errors else []
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@message_bp.route('/api/messages/<message_id>/status', methods=['GET'])
@login_required
def get_message_status(message_id):
    """Get message sending status"""
    message = get_document(MESSAGES_COLLECTION, message_id)
    
    if not message:
        return jsonify({'error': 'Message not found'}), 404
    
    # Verify message belongs to user (or is admin)
    if message.get('user_id') != session['user_id'] and session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'message': message,
        'stats': message.get('stats', {})
    })


@message_bp.route('/api/messages/<message_id>/recipients', methods=['GET'])
@login_required
def get_message_recipients(message_id):
    """Get message recipients with status"""
    message = get_document(MESSAGES_COLLECTION, message_id)
    
    if not message:
        return jsonify({'error': 'Message not found'}), 404
    
    # Verify message belongs to user (or is admin)
    if message.get('user_id') != session['user_id'] and session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get pagination params
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Get recipients
    recipients = query_documents(MESSAGE_RECIPIENTS_COLLECTION, 'message_id', '==', message_id)
    
    # Sort by created_at
    recipients.sort(key=lambda x: x.get('created_at', ''))
    
    # Paginate
    total = len(recipients)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_recipients = recipients[start:end]
    
    return jsonify({
        'recipients': paginated_recipients,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

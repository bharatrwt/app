from flask import Blueprint, request, jsonify
from config import Config
from firebase_utils import (
    get_document, update_document, query_documents,
    MESSAGES_COLLECTION, MESSAGE_RECIPIENTS_COLLECTION
)
from datetime import datetime
import hmac
import hashlib
import logging

webhook_bp = Blueprint('webhooks', __name__)
logger = logging.getLogger(__name__)


def verify_webhook_signature(payload, signature):
    """Verify Meta webhook signature using App Secret"""
    # Meta sends signature in X-Hub-Signature-256 header
    # Format: sha256=<signature>
    if not signature:
        return False
    
    if not Config.META_APP_SECRET:
        logger.error("META_APP_SECRET not configured - webhook signature verification disabled")
        return False
    
    expected_signature = hmac.new(
        Config.META_APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    return hmac.compare_digest(expected_signature, signature)


@webhook_bp.route('/meta', methods=['GET'])
def verify_webhook():
    """Verify webhook endpoint (Meta requirement)"""
    # Meta sends these parameters for verification
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == Config.META_WEBHOOK_VERIFY_TOKEN:
        logger.info('Webhook verified successfully')
        return challenge, 200
    else:
        logger.warning('Webhook verification failed')
        return 'Forbidden', 403


@webhook_bp.route('/meta', methods=['POST'])
def handle_webhook():
    """Handle Meta webhook events for message status updates"""
    try:
        # Get signature for verification
        signature = request.headers.get('X-Hub-Signature-256')
        
        # Verify signature
        if not verify_webhook_signature(request.get_data(), signature):
            logger.warning('Invalid webhook signature')
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Parse webhook payload
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process webhook entries
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                
                # Get messages or statuses
                messages = value.get('messages', [])
                statuses = value.get('statuses', [])
                
                # Process message replies
                for message in messages:
                    process_message_reply(message)
                
                # Process status updates
                for status in statuses:
                    process_status_update(status)
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        logger.error(f'Webhook error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


def process_message_reply(message):
    """Process incoming message (reply from recipient)"""
    try:
        recipient_phone = message.get('from')
        message_text = message.get('text', {}).get('body', '')
        timestamp = message.get('timestamp')
        
        # Find message recipient by phone number
        recipients = query_documents(
            MESSAGE_RECIPIENTS_COLLECTION,
            'phone_number',
            '==',
            f"+{recipient_phone}" if not recipient_phone.startswith('+') else recipient_phone
        )
        
        for recipient in recipients:
            # Update recipient with reply
            update_data = {
                'reply_text': message_text,
                'reply_at': datetime.fromtimestamp(int(timestamp)).isoformat() if timestamp else datetime.utcnow().isoformat()
            }
            
            update_document(MESSAGE_RECIPIENTS_COLLECTION, recipient['id'], update_data)
            
            # Update message stats
            message_id = recipient.get('message_id')
            if message_id:
                message = get_document(MESSAGES_COLLECTION, message_id)
                if message:
                    stats = message.get('stats', {})
                    stats['replied'] = stats.get('replied', 0) + 1
                    update_document(MESSAGES_COLLECTION, message_id, {'stats': stats})
            
            logger.info(f'Processed reply from {recipient_phone}')
    
    except Exception as e:
        logger.error(f'Error processing message reply: {str(e)}')


def process_status_update(status):
    """Process message status update (sent, delivered, read)"""
    try:
        recipient_phone = status.get('recipient_id')
        status_type = status.get('status')
        timestamp = status.get('timestamp')
        message_id_meta = status.get('id')  # Meta's message ID
        
        # Map status types
        status_map = {
            'sent': 'sent',
            'delivered': 'delivered',
            'read': 'seen',
            'failed': 'failed'
        }
        
        new_status = status_map.get(status_type)
        if not new_status:
            return
        
        # Find message recipient by phone number and recent timestamp
        recipients = query_documents(
            MESSAGE_RECIPIENTS_COLLECTION,
            'phone_number',
            '==',
            f"+{recipient_phone}" if not recipient_phone.startswith('+') else recipient_phone
        )
        
        for recipient in recipients:
            # Only update if status is progressing forward
            current_status = recipient.get('status', 'queued')
            status_order = ['queued', 'sent', 'delivered', 'seen']
            
            if new_status == 'failed':
                should_update = True
            elif current_status in status_order and new_status in status_order:
                should_update = status_order.index(new_status) > status_order.index(current_status)
            else:
                should_update = True
            
            if should_update:
                update_data = {
                    'status': new_status,
                    'meta': {
                        **recipient.get('meta', {}),
                        'message_id_meta': message_id_meta,
                        'last_updated': datetime.utcnow().isoformat()
                    }
                }
                
                # Add timestamp fields
                if new_status == 'delivered':
                    update_data['delivered_at'] = datetime.fromtimestamp(int(timestamp)).isoformat() if timestamp else datetime.utcnow().isoformat()
                elif new_status == 'seen':
                    update_data['seen_at'] = datetime.fromtimestamp(int(timestamp)).isoformat() if timestamp else datetime.utcnow().isoformat()
                
                update_document(MESSAGE_RECIPIENTS_COLLECTION, recipient['id'], update_data)
                
                # Update message stats
                message_id = recipient.get('message_id')
                if message_id:
                    message = get_document(MESSAGES_COLLECTION, message_id)
                    if message:
                        stats = message.get('stats', {})
                        
                        # Decrement old status count
                        if current_status in stats:
                            stats[current_status] = max(0, stats.get(current_status, 0) - 1)
                        
                        # Increment new status count
                        stats[new_status] = stats.get(new_status, 0) + 1
                        
                        update_document(MESSAGES_COLLECTION, message_id, {'stats': stats})
                
                logger.info(f'Updated status for {recipient_phone} to {new_status}')
    
    except Exception as e:
        logger.error(f'Error processing status update: {str(e)}')

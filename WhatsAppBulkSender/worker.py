import time
import logging
from rq import Queue
from redis import Redis
from config import Config
from firebase_utils import (
    get_document, update_document,
    BUSINESSES_COLLECTION, MESSAGES_COLLECTION, MESSAGE_RECIPIENTS_COLLECTION
)
from whatsapp_adapter import WhatsAppAdapter
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis connection
try:
    redis_conn = Redis.from_url(Config.REDIS_URL)
    queue = Queue(connection=redis_conn, default_timeout=600)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    # Fallback: create a mock queue for development
    redis_conn = None
    queue = None


def queue_message_job(message_id, business_id, recipient_ids):
    """Queue a message sending job"""
    if queue:
        job = queue.enqueue(
            process_message_batch,
            message_id,
            business_id,
            recipient_ids,
            job_timeout=600
        )
        logger.info(f"Queued job {job.id} for message {message_id}")
        return job.id
    else:
        # For development without Redis: process synchronously
        logger.warning("Redis not available, processing synchronously")
        process_message_batch(message_id, business_id, recipient_ids)
        return "sync"


def process_message_batch(message_id, business_id, recipient_ids):
    """Process a batch of message recipients"""
    try:
        logger.info(f"Processing message {message_id} for {len(recipient_ids)} recipients")
        
        # Get message details
        message = get_document(MESSAGES_COLLECTION, message_id)
        if not message:
            logger.error(f"Message {message_id} not found")
            return
        
        # Get business details
        business = get_document(BUSINESSES_COLLECTION, business_id)
        if not business:
            logger.error(f"Business {business_id} not found")
            return
        
        # Create WhatsApp adapter
        adapter = WhatsAppAdapter.create_adapter_from_business(business)
        
        media_url = message.get('media_url')
        title = message.get('title')
        body = message.get('body')
        
        # Process recipients in batches
        batch_size = Config.BATCH_SIZE
        success_count = 0
        failed_count = 0
        
        for i in range(0, len(recipient_ids), batch_size):
            batch = recipient_ids[i:i + batch_size]
            
            for recipient_id in batch:
                # Get recipient details
                recipient = get_document(MESSAGE_RECIPIENTS_COLLECTION, recipient_id)
                if not recipient:
                    continue
                
                phone_number = recipient.get('phone_number')
                
                # Send message with retry logic
                result = send_with_retry(
                    adapter,
                    phone_number,
                    media_url,
                    title,
                    body,
                    max_retries=Config.MAX_RETRIES
                )
                
                if result['success']:
                    # Update recipient status
                    update_document(MESSAGE_RECIPIENTS_COLLECTION, recipient_id, {
                        'status': 'sent',
                        'meta': {
                            'message_id_meta': result.get('message_id'),
                            'sent_at': datetime.utcnow().isoformat()
                        }
                    })
                    success_count += 1
                else:
                    # Update recipient as failed
                    update_document(MESSAGE_RECIPIENTS_COLLECTION, recipient_id, {
                        'status': 'failed',
                        'meta': {
                            'error': result.get('message'),
                            'failed_at': datetime.utcnow().isoformat()
                        }
                    })
                    failed_count += 1
                
                # Small delay to respect rate limits
                time.sleep(0.1)
            
            # Update message stats after each batch
            update_message_stats(message_id)
            
            # Delay between batches
            if i + batch_size < len(recipient_ids):
                time.sleep(1)
        
        # Final stats update
        update_message_stats(message_id)
        
        # Update message status
        update_document(MESSAGES_COLLECTION, message_id, {
            'status': 'completed'
        })
        
        logger.info(f"Completed message {message_id}: {success_count} sent, {failed_count} failed")
    
    except Exception as e:
        logger.error(f"Error processing message batch: {str(e)}")
        # Update message status as failed
        update_document(MESSAGES_COLLECTION, message_id, {
            'status': 'failed',
            'error': str(e)
        })


def send_with_retry(adapter, phone_number, media_url, title, body, max_retries=3):
    """Send message with retry logic"""
    for attempt in range(max_retries):
        result = adapter.send_message(phone_number, media_url, title, body)
        
        if result['success']:
            return result
        
        # Check if error is retryable
        error_type = result.get('error')
        if error_type in ['timeout', 'connection_error', 'rate_limit']:
            # Wait with exponential backoff
            wait_time = (2 ** attempt) * 1
            if error_type == 'rate_limit':
                wait_time = max(wait_time, int(result.get('retry_after', 60)))
            
            logger.warning(f"Retrying {phone_number} after {wait_time}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        else:
            # Permanent error, don't retry
            logger.error(f"Permanent error for {phone_number}: {result.get('message')}")
            return result
    
    # All retries failed
    return result


def update_message_stats(message_id):
    """Update message statistics by counting recipients"""
    from firebase_utils import query_documents
    
    recipients = query_documents(MESSAGE_RECIPIENTS_COLLECTION, 'message_id', '==', message_id)
    
    stats = {
        'queued': 0,
        'sent': 0,
        'delivered': 0,
        'seen': 0,
        'failed': 0,
        'replied': 0
    }
    
    for recipient in recipients:
        status = recipient.get('status', 'queued')
        if status in stats:
            stats[status] += 1
        
        # Count replies
        if recipient.get('reply_text'):
            stats['replied'] += 1
    
    update_document(MESSAGES_COLLECTION, message_id, {'stats': stats})


if __name__ == '__main__':
    # Run worker
    if queue:
        from rq import Worker
        worker = Worker([queue], connection=redis_conn)
        logger.info("Starting RQ worker...")
        worker.work()
    else:
        logger.error("Cannot start worker: Redis connection not available")

import requests
import logging
from config import Config
from admin_routes import decrypt_token

logger = logging.getLogger(__name__)


class WhatsAppAdapter:
    """Adapter for Meta WhatsApp Business Cloud API"""
    
    def __init__(self, business_token, phone_id, waba_id):
        """Initialize WhatsApp adapter with business credentials"""
        self.business_token = business_token
        self.phone_id = phone_id
        self.waba_id = waba_id
        self.base_url = Config.META_API_BASE_URL
    
    def send_message(self, to_number, media_url, title, body):
        """Send a WhatsApp message with media and text"""
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.business_token}',
                'Content-Type': 'application/json'
            }
            
            # Construct message payload
            # First send media (image) with caption
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': to_number,
                'type': 'image',
                'image': {
                    'link': media_url,
                    'caption': f"{title}\n\n{body}"
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Log response
            logger.info(f"WhatsApp API response for {to_number}: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'response': result
                }
            elif response.status_code == 429:
                # Rate limit exceeded
                return {
                    'success': False,
                    'error': 'rate_limit',
                    'message': 'Rate limit exceeded',
                    'retry_after': response.headers.get('Retry-After', 60)
                }
            else:
                error_data = response.json()
                return {
                    'success': False,
                    'error': 'api_error',
                    'message': error_data.get('error', {}).get('message', 'Unknown error'),
                    'error_data': error_data
                }
        
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'timeout',
                'message': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'connection_error',
                'message': 'Connection error'
            }
        except Exception as e:
            logger.error(f"Error sending message to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': 'exception',
                'message': str(e)
            }
    
    def send_text_message(self, to_number, text):
        """Send a text-only message"""
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.business_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': to_number,
                'type': 'text',
                'text': {
                    'body': text
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('messages', [{}])[0].get('id'),
                    'response': result
                }
            else:
                error_data = response.json()
                return {
                    'success': False,
                    'error': 'api_error',
                    'message': error_data.get('error', {}).get('message', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error sending text message to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': 'exception',
                'message': str(e)
            }
    
    @staticmethod
    def create_adapter_from_business(business):
        """Create WhatsApp adapter from business document"""
        # Decrypt the business token
        decrypted_token = decrypt_token(business.get('business_token'))
        
        return WhatsAppAdapter(
            business_token=decrypted_token,
            phone_id=business.get('phone_id'),
            waba_id=business.get('waba_id')
        )

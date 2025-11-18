import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SESSION_SECRET")
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    # Meta WhatsApp API Configuration
    META_API_VERSION = "v17.0"
    META_API_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"
    META_WEBHOOK_VERIFY_TOKEN = os.environ.get("META_WEBHOOK_VERIFY_TOKEN", "your_webhook_verify_token")
    META_APP_SECRET = os.environ.get("META_APP_SECRET")  # Required for webhook signature verification
    
    # Encryption Configuration (REQUIRED - must be set in environment)
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
    
    # Redis Configuration for RQ
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # Message Processing Configuration
    BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
    
    # File Upload Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"csv", "xlsx"}

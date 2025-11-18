"""
Seed initial data for the WhatsApp Bulk Messaging System

This script creates:
1. An initial admin user
2. Optional sample businesses and users for testing

Run: python seed_data.py
"""

from werkzeug.security import generate_password_hash
from firebase_utils import create_document, query_documents, USERS_COLLECTION, BUSINESSES_COLLECTION
from datetime import datetime
import os
from cryptography.fernet import Fernet


def create_admin_user(email="admin@example.com", password="admin123", name="Admin User"):
    """Create an admin user if it doesn't exist"""
    existing_users = query_documents(USERS_COLLECTION, 'email', '==', email)
    
    if existing_users:
        print(f"Admin user {email} already exists!")
        return existing_users[0]['id']
    
    user_data = {
        'name': name,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': 'admin',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    user_id = create_document(USERS_COLLECTION, user_data)
    print(f"✓ Created admin user: {email} / {password}")
    return user_id


def create_sample_business(name="Sample Business"):
    """Create a sample business for testing"""
    # Get encryption key from environment - REQUIRED
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    if not encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY environment variable is required. "
            "Generate one using: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    
    cipher_suite = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    # Encrypt sample token
    sample_token = "SAMPLE_TOKEN_REPLACE_WITH_REAL_TOKEN"
    encrypted_token = cipher_suite.encrypt(sample_token.encode()).decode()
    
    business_data = {
        'business_name': name,
        'business_token': encrypted_token,
        'phone_id': 'SAMPLE_PHONE_ID',
        'waba_id': 'SAMPLE_WABA_ID',
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    business_id = create_document(BUSINESSES_COLLECTION, business_data)
    print(f"✓ Created sample business: {name}")
    print(f"  Note: Please update business_token, phone_id, and waba_id with real credentials!")
    return business_id


def create_sample_user(email="user@example.com", password="user123", name="Test User"):
    """Create a sample regular user"""
    existing_users = query_documents(USERS_COLLECTION, 'email', '==', email)
    
    if existing_users:
        print(f"User {email} already exists!")
        return existing_users[0]['id']
    
    user_data = {
        'name': name,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': 'user',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    user_id = create_document(USERS_COLLECTION, user_data)
    print(f"✓ Created sample user: {email} / {password}")
    return user_id


if __name__ == '__main__':
    print("=" * 50)
    print("WhatsApp Bulk Messaging System - Seed Data")
    print("=" * 50)
    
    # Create admin user
    print("\n1. Creating admin user...")
    admin_id = create_admin_user()
    
    # Ask if user wants sample data
    create_samples = input("\nCreate sample business and user for testing? (y/n): ").lower()
    
    if create_samples == 'y':
        print("\n2. Creating sample business...")
        business_id = create_sample_business()
        
        print("\n3. Creating sample user...")
        user_id = create_sample_user()
        
        print("\n" + "=" * 50)
        print("Sample Data Created Successfully!")
        print("=" * 50)
        print("\nLogin Credentials:")
        print("  Admin: admin@example.com / admin123")
        print("  User:  user@example.com / user123")
        print("\nNEXT STEPS:")
        print("1. Update the sample business credentials in the admin panel")
        print("2. Create a task and assign it to the sample user")
        print("3. Login as user and send test messages")
    else:
        print("\n" + "=" * 50)
        print("Admin User Created Successfully!")
        print("=" * 50)
        print("\nLogin Credentials:")
        print("  Admin: admin@example.com / admin123")
    
    print("\n")

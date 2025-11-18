import firebase_admin
from firebase_admin import credentials, firestore
from config import Config
import os


# Initialize Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        if os.path.exists(Config.FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        else:
            # For development: use default credentials or environment variable
            firebase_admin.initialize_app()
    
    return firestore.client()


# Get Firestore client
db = None


def get_db():
    global db
    if db is None:
        db = initialize_firebase()
    return db


# Collection names
USERS_COLLECTION = "users"
BUSINESSES_COLLECTION = "businesses"
TASKS_COLLECTION = "tasks"
MESSAGES_COLLECTION = "messages"
MESSAGE_RECIPIENTS_COLLECTION = "message_recipients"
AUDIT_LOGS_COLLECTION = "audit_logs"


# Helper functions for CRUD operations
def create_document(collection_name, data, doc_id=None):
    """Create a new document in Firestore"""
    db = get_db()
    collection_ref = db.collection(collection_name)
    
    if doc_id:
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(data)
        return doc_id
    else:
        doc_ref = collection_ref.add(data)
        return doc_ref[1].id


def get_document(collection_name, doc_id):
    """Get a document by ID"""
    db = get_db()
    doc_ref = db.collection(collection_name).document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None


def update_document(collection_name, doc_id, data):
    """Update a document"""
    db = get_db()
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.update(data)
    return True


def delete_document(collection_name, doc_id):
    """Delete a document"""
    db = get_db()
    db.collection(collection_name).document(doc_id).delete()
    return True


def get_all_documents(collection_name, filters=None, limit=None, order_by=None):
    """Get all documents from a collection with optional filters"""
    db = get_db()
    query = db.collection(collection_name)
    
    if filters:
        for field, operator, value in filters:
            query = query.where(field, operator, value)
    
    if order_by:
        query = query.order_by(order_by)
    
    if limit:
        query = query.limit(limit)
    
    docs = query.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(data)
    
    return results


def query_documents(collection_name, field, operator, value):
    """Query documents by a specific field"""
    db = get_db()
    docs = db.collection(collection_name).where(field, operator, value).stream()
    
    results = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(data)
    
    return results


def create_audit_log(user_id, action, object_type, object_id, details):
    """Create an audit log entry"""
    from datetime import datetime
    
    log_data = {
        'user_id': user_id,
        'action': action,
        'object_type': object_type,
        'object_id': object_id,
        'details': details,
        'created_at': datetime.utcnow().isoformat()
    }
    
    return create_document(AUDIT_LOGS_COLLECTION, log_data)

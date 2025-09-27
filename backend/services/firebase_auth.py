import firebase_admin
from firebase_admin import auth, credentials
from functools import wraps
from flask import request, jsonify
import logging
import os

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not service_account_path:
                logging.error("GOOGLE_APPLICATION_CREDENTIALS not set")
                return False
            
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logging.info("✅ Firebase Admin SDK initialized")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        return False


def verify_firebase_token(token):
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'email_verified': decoded_token.get('email_verified', False)
        }
    except Exception as e:
        logging.error(f"Token verification failed: {str(e)}")
        return None


def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Authorization header missing or invalid',
                'status': 'error'
            }), 401
        
        token = auth_header.split('Bearer ')[1]
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({
                'error': 'Invalid or expired token',
                'status': 'error'
            }), 401
        
        request.current_user = user_info
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    return getattr(request, 'current_user', None)


def get_current_firebase_uid():
    current_user = get_current_user()
    return current_user['uid'] if current_user else None

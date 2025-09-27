"""
Firebase Authentication Service for TikTalk API
"""

import firebase_admin
from firebase_admin import auth, credentials
from functools import wraps
from flask import request, jsonify
import logging
import os
from dotenv import load_dotenv

load_dotenv()
# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            # Get the path to the service account key from environment
            service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            
            if not service_account_path:
                logging.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
                return False
            
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logging.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logging.warning(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        return False

def verify_firebase_token(token):
    """
    Verify Firebase ID token and return user info
    
    Args:
        token (str): Firebase ID token
        
    Returns:
        dict: User information if token is valid, None otherwise
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)
        
        return {
            'uid': decoded_token['uid'],  # Firebase UID
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'email_verified': decoded_token.get('email_verified', False)
        }
    except Exception as e:
        logging.error(f"Token verification failed: {str(e)}")
        return None

def require_auth(f):
    """
    Decorator to require Firebase authentication for API endpoints
    
    Usage:
        @require_auth
        def protected_endpoint():
            current_user = request.current_user  # Contains Firebase user info
            firebase_uid = current_user['uid']
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'Authorization header missing or invalid',
                    'message': 'Please provide a valid Bearer token',
                    'status': 'error'
                }), 401
            
            # Extract token
            token = auth_header.split('Bearer ')[1]
            
            # Verify token
            user_info = verify_firebase_token(token)
            if not user_info:
                return jsonify({
                    'error': 'Invalid or expired token',
                    'message': 'Please log in again',
                    'status': 'error'
                }), 401
            
            # Add user info to request context
            request.current_user = user_info
            
            # Continue to the actual endpoint
            return f(*args, **kwargs)
            
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Please try logging in again',
                'status': 'error'
            }), 500
    
    return decorated_function

def get_current_user():
    """
    Get current user from request context
    
    Returns:
        dict: Current user information or None
    """
    return getattr(request, 'current_user', None)

def get_current_firebase_uid():
    """
    Get current user's Firebase UID from request context
    
    Returns:
        str: Firebase UID or None
    """
    current_user = get_current_user()
    return current_user['uid'] if current_user else None

def require_email_verified(f):
    """
    Decorator to require email verification in addition to authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check authentication
        auth_result = require_auth(f)(*args, **kwargs)
        
        # If authentication failed, return the error
        if isinstance(auth_result, tuple) and auth_result[1] in [401, 500]:
            return auth_result
        
        # Check if email is verified
        current_user = get_current_user()
        if not current_user.get('email_verified', False):
            return jsonify({
                'error': 'Email not verified',
                'message': 'Please verify your email address before accessing this resource',
                'status': 'error'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

# Initialize Firebase when module is imported
initialize_firebase()

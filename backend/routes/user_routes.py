from flask import Blueprint, request, jsonify
from models.user import User
from services.firebase_auth import require_auth, get_current_firebase_uid, get_current_user
import re
import logging

user_bp = Blueprint('users', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format (alphanumeric and underscores only, 3-20 chars)"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

@user_bp.route('/users/register', methods=['POST'])
@require_auth
def register_user():
    """
    Register a new user with Firebase UID
    Expected JSON: {"email": "string", "full_name": "string", "username": "string" (optional)}
    """
    try:
        data = request.get_json()
        print(data)
        current_user = get_current_user()
        firebase_uid = current_user['uid']
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'full_name']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error'
            }), 400
        
        email = data['email'].strip().lower()
        full_name = data['full_name'].strip()
        username = data.get('username', '').strip() if data.get('username') else None
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format',
                'status': 'error'
            }), 400
        
        # Validate full name
        if len(full_name) < 2 or len(full_name) > 100:
            return jsonify({
                'error': 'Full name must be between 2 and 100 characters',
                'status': 'error'
            }), 400
        
        # Validate username if provided
        if username:
            if not validate_username(username):
                return jsonify({
                    'error': 'Username must be 3-20 characters long and contain only letters, numbers, and underscores',
                    'status': 'error'
                }), 400
            
            # Check if username already exists
            existing_user = User.get_by_username(username)
            if existing_user:
                return jsonify({
                    'error': 'Username already exists',
                    'status': 'error'
                }), 409
        
        # Check if email already exists
        existing_email = User.get_by_email(email)
        if existing_email:
            return jsonify({
                'error': 'Email already exists',
                'status': 'error'
            }), 409
        
        # Check if Firebase UID already exists
        existing_firebase_user = User.get_by_firebase_uid(firebase_uid)
        if existing_firebase_user:
            return jsonify({
                'error': 'User already registered',
                'status': 'error'
            }), 409
        
        # Create new user
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            full_name=full_name,
            username=username
        )
        result = user.save()
        
        if result['success']:
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict(),
                'status': 'success'
            }), 201
        else:
            return jsonify({
                'error': f'Failed to register user: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error registering user: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@user_bp.route('/users/me', methods=['GET'])
@require_auth
def get_current_user_profile():
    """Get current user's profile"""
    try:
        firebase_uid = get_current_firebase_uid()
        user = User.get_by_firebase_uid(firebase_uid)
        
        if user:
            return jsonify({
                'user': user.to_dict(),
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': 'User not found. Please register first.',
                'status': 'error'
            }), 404
            
    except Exception as e:
        logging.error(f"Error getting current user: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@user_bp.route('/users/me', methods=['PUT'])
@require_auth
def update_current_user_profile():
    """Update current user's profile"""
    try:
        data = request.get_json()
        firebase_uid = get_current_firebase_uid()
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Get existing user
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({
                'error': 'User not found. Please register first.',
                'status': 'error'
            }), 404
        
        # Update fields if provided
        if 'email' in data and data['email']:
            email = data['email'].strip().lower()
            if not validate_email(email):
                return jsonify({
                    'error': 'Invalid email format',
                    'status': 'error'
                }), 400
            
            # Check if email is already taken by another user
            existing_email = User.get_by_email(email)
            if existing_email and existing_email.firebase_uid != firebase_uid:
                return jsonify({
                    'error': 'Email already exists',
                    'status': 'error'
                }), 409
            
            user.email = email
        
        if 'full_name' in data and data['full_name']:
            full_name = data['full_name'].strip()
            if len(full_name) < 2 or len(full_name) > 100:
                return jsonify({
                    'error': 'Full name must be between 2 and 100 characters',
                    'status': 'error'
                }), 400
            user.full_name = full_name
        
        if 'username' in data and data['username']:
            username = data['username'].strip()
            if username:  # Only validate if username is provided
                if not validate_username(username):
                    return jsonify({
                        'error': 'Username must be 3-20 characters long and contain only letters, numbers, and underscores',
                        'status': 'error'
                    }), 400
                
                # Check if username is already taken by another user
                existing_username = User.get_by_username(username)
                if existing_username and existing_username.firebase_uid != firebase_uid:
                    return jsonify({
                        'error': 'Username already exists',
                        'status': 'error'
                    }), 409
                
                user.username = username
            else:
                user.username = None  # Remove username if empty string provided
        
        # Save updated user
        result = user.save()
        
        if result['success']:
            return jsonify({
                'message': 'User profile updated successfully',
                'user': user.to_dict(),
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to update user profile: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating user profile: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@user_bp.route('/users/<firebase_uid>', methods=['GET'])
@require_auth
def get_user_by_firebase_uid(firebase_uid):
    """Get user by Firebase UID (for admin or self-access)"""
    try:
        current_firebase_uid = get_current_firebase_uid()
        
        # Users can only access their own profile or admin can access any
        if firebase_uid != current_firebase_uid:
            # TODO: Add admin check here if needed
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        user = User.get_by_firebase_uid(firebase_uid)
        
        if user:
            return jsonify({
                'user': user.to_dict(),
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': 'User not found',
                'status': 'error'
            }), 404
            
    except Exception as e:
        logging.error(f"Error getting user: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@user_bp.route('/users/me', methods=['DELETE'])
@require_auth
def delete_current_user():
    """Delete current user's account"""
    try:
        firebase_uid = get_current_firebase_uid()
        user = User.get_by_firebase_uid(firebase_uid)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'status': 'error'
            }), 404
        
        # Delete user from database (cascade will handle related records)
        delete_query = "DELETE FROM users WHERE firebase_uid = %s"
        from services.database_service import db_service
        result = db_service.execute_query(delete_query, (firebase_uid,))
        
        if result['success']:
            return jsonify({
                'message': 'User account deleted successfully',
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to delete user account: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error deleting user: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500
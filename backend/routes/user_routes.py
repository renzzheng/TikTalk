from flask import Blueprint, request, jsonify
from models.user import User
from services.database_service import db_service
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

@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user
    Expected JSON: {"username": "string", "email": "string", "full_name": "string"}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Validate required fields
        required_fields = ['username', 'email', 'full_name']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error'
            }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        full_name = data['full_name'].strip()
        
        # Validate input formats
        if not validate_username(username):
            return jsonify({
                'error': 'Username must be 3-20 characters long and contain only letters, numbers, and underscores',
                'status': 'error'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format',
                'status': 'error'
            }), 400
        
        if len(full_name) < 2 or len(full_name) > 100:
            return jsonify({
                'error': 'Full name must be between 2 and 100 characters',
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
        
        # Create new user
        user = User(username=username, email=email, full_name=full_name)
        result = user.save()
        
        if result['success']:
            return jsonify({
                'message': 'User created successfully',
                'user': user.to_dict(),
                'status': 'success'
            }), 201
        else:
            return jsonify({
                'error': f'Failed to create user: {result["error"]}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@user_bp.route('/users/<username>', methods=['GET'])
def get_user(username):
    """Get user by username"""
    try:
        user = User.get_by_username(username)
        
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

from flask import Blueprint, request, jsonify
from models.notes import Notes, NotesStatus
from models.user import User
from services.firebase_auth import require_auth, get_current_firebase_uid, get_current_user
import logging
import re

notes_bp = Blueprint('notes', __name__)

def validate_gcs_url(url):
    """Validate Google Cloud Storage URL format"""
    gcs_patterns = [
        r'^gs://[a-zA-Z0-9._-]+/.*',  # gs://bucket/path
        r'^https://storage\.googleapis\.com/[a-zA-Z0-9._-]+/.*',  # https://storage.googleapis.com/bucket/path
        r'^https://storage\.cloud\.google\.com/[a-zA-Z0-9._-]+/.*'  # https://storage.cloud.google.com/bucket/path
    ]
    
    for pattern in gcs_patterns:
        if re.match(pattern, url):
            return True
    return False

def validate_status(status):
    """Validate status value"""
    valid_statuses = [status.value for status in NotesStatus]
    return status in valid_statuses

@notes_bp.route('/notes', methods=['POST'])
@require_auth
def create_notes():
    """
    Create new notes
    Expected JSON: {"notes_link": "string", "status": "string" (optional)}
    """
    try:
        data = request.get_json()
        current_user = get_current_user()
        firebase_uid = current_user['uid']
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Validate required fields
        if 'notes_link' not in data or not data['notes_link']:
            return jsonify({
                'error': 'Missing required field: notes_link',
                'status': 'error'
            }), 400
        
        notes_link = data['notes_link'].strip()
        status = data.get('status', 'not_started').strip()
        
        # Check if user exists in our database
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({
                'error': 'User not registered. Please register first.',
                'status': 'error'
            }), 404
        
        # Validate Google Cloud Storage URL
        if not validate_gcs_url(notes_link):
            return jsonify({
                'error': 'Invalid Google Cloud Storage URL format',
                'status': 'error'
            }), 400
        
        # Validate status
        if not validate_status(status):
            valid_statuses = [status.value for status in NotesStatus]
            return jsonify({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                'status': 'error'
            }), 400
        
        # Create new notes
        notes = Notes(firebase_uid=firebase_uid, notes_link=notes_link, status=status)
        result = notes.save()
        
        if result['success']:
            return jsonify({
                'message': 'Notes created successfully',
                'notes': notes.to_dict(),
                'status': 'success'
            }), 201
        else:
            return jsonify({
                'error': f'Failed to create notes: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error creating notes: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/<int:notes_id>', methods=['GET'])
@require_auth
def get_notes(notes_id):
    """Get notes by ID"""
    try:
        notes = Notes.get_by_id(notes_id)
        current_firebase_uid = get_current_firebase_uid()
        
        if not notes:
            return jsonify({
                'error': 'Notes not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this notes
        if notes.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'notes': notes.to_dict(include_user=include_user),
            'status': 'success'
        }), 200
            
    except Exception as e:
        logging.error(f"Error getting notes: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/my-notes', methods=['GET'])
@require_auth
def get_my_notes():
    """Get current user's notes"""
    try:
        firebase_uid = get_current_firebase_uid()
        
        # Check if user exists in our database
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({
                'error': 'User not registered. Please register first.',
                'status': 'error'
            }), 404
        
        notes = Notes.get_by_firebase_uid(firebase_uid)
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'notes': [note.to_dict(include_user=include_user) for note in notes],
            'count': len(notes),
            'firebase_uid': firebase_uid,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting user notes: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/status/<status>', methods=['GET'])
@require_auth
def get_notes_by_status(status):
    """Get all notes by status (user's notes only)"""
    try:
        firebase_uid = get_current_firebase_uid()
        
        # Validate status
        if not validate_status(status):
            valid_statuses = [status.value for status in NotesStatus]
            return jsonify({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                'status': 'error'
            }), 400
        
        # Get user's notes with specific status
        all_notes = Notes.get_by_firebase_uid(firebase_uid)
        notes = [note for note in all_notes if note.status == status]
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'notes': [note.to_dict(include_user=include_user) for note in notes],
            'count': len(notes),
            'status_filter': status,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting notes by status: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes', methods=['GET'])
@require_auth
def get_all_notes():
    """Get all notes (user's notes only)"""
    try:
        firebase_uid = get_current_firebase_uid()
        
        notes = Notes.get_by_firebase_uid(firebase_uid)
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'notes': [note.to_dict(include_user=include_user) for note in notes],
            'count': len(notes),
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting all notes: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/<int:notes_id>', methods=['PUT'])
@require_auth
def update_notes(notes_id):
    """Update notes by ID"""
    try:
        data = request.get_json()
        current_firebase_uid = get_current_firebase_uid()
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Get existing notes
        notes = Notes.get_by_id(notes_id)
        if not notes:
            return jsonify({
                'error': 'Notes not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this notes
        if notes.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        # Update fields if provided
        if 'notes_link' in data and data['notes_link']:
            notes_link = data['notes_link'].strip()
            if not validate_gcs_url(notes_link):
                return jsonify({
                    'error': 'Invalid Google Cloud Storage URL format',
                    'status': 'error'
                }), 400
            notes.notes_link = notes_link
        
        if 'status' in data and data['status']:
            status = data['status'].strip()
            if not validate_status(status):
                valid_statuses = [status.value for status in NotesStatus]
                return jsonify({
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                    'status': 'error'
                }), 400
            notes.status = status
        
        # Save updated notes
        result = notes.update()
        
        if result['success']:
            return jsonify({
                'message': 'Notes updated successfully',
                'notes': notes.to_dict(),
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to update notes: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating notes: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/<int:notes_id>/status', methods=['PATCH'])
@require_auth
def update_notes_status(notes_id):
    """Update only the status of notes"""
    try:
        data = request.get_json()
        current_firebase_uid = get_current_firebase_uid()
        
        if not data or 'status' not in data:
            return jsonify({
                'error': 'Request body must contain status field',
                'status': 'error'
            }), 400
        
        # Get existing notes
        notes = Notes.get_by_id(notes_id)
        if not notes:
            return jsonify({
                'error': 'Notes not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this notes
        if notes.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        new_status = data['status'].strip()
        
        # Validate status
        if not validate_status(new_status):
            valid_statuses = [status.value for status in NotesStatus]
            return jsonify({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                'status': 'error'
            }), 400
        
        # Update status
        result = notes.update_status(new_status)
        
        if result['success']:
            return jsonify({
                'message': 'Notes status updated successfully',
                'notes': notes.to_dict(),
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to update notes status: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating notes status: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/<int:notes_id>', methods=['DELETE'])
@require_auth
def delete_notes(notes_id):
    """Delete notes by ID"""
    try:
        current_firebase_uid = get_current_firebase_uid()
        
        # Get existing notes
        notes = Notes.get_by_id(notes_id)
        if not notes:
            return jsonify({
                'error': 'Notes not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this notes
        if notes.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        result = Notes.delete_by_id(notes_id)
        
        if result['success']:
            return jsonify({
                'message': 'Notes deleted successfully',
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to delete notes: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error deleting notes: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@notes_bp.route('/notes/statuses', methods=['GET'])
def get_available_statuses():
    """Get all available status values (public endpoint)"""
    try:
        statuses = [status.value for status in NotesStatus]
        
        return jsonify({
            'statuses': statuses,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting available statuses: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500
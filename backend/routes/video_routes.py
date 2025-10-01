from flask import Blueprint, request, jsonify
from models.video import Video
from models.user import User
from services.firebase_auth import require_auth, get_current_firebase_uid, get_current_user
import logging
import re

video_bp = Blueprint('videos', __name__)

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

@video_bp.route('/videos', methods=['POST'])
@require_auth
def create_video():
    """
    Create a new video
    Expected JSON: {"videos_link": "string"}
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
        if 'videos_link' not in data or not data['videos_link']:
            return jsonify({
                'error': 'Missing required field: videos_link',
                'status': 'error'
            }), 400
        
        videos_link = data['videos_link'].strip()
        
        # Validate Google Cloud Storage URL
        if not validate_gcs_url(videos_link):
            return jsonify({
                'error': 'Invalid Google Cloud Storage URL format',
                'status': 'error'
            }), 400
        
        # Check if user exists in our database
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({
                'error': 'User not registered. Please register first.',
                'status': 'error'
            }), 404
        
        # Create new video
        video = Video(firebase_uid=firebase_uid, videos_link=videos_link)
        result = video.save()
        
        if result['success']:
            return jsonify({
                'message': 'Video created successfully',
                'video': video.to_dict(),
                'status': 'success'
            }), 201
        else:
            return jsonify({
                'error': f'Failed to create video: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error creating video: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@video_bp.route('/videos/<int:video_id>', methods=['GET'])
@require_auth
def get_video(video_id):
    """Get video by ID"""
    try:
        print(f"Fetching video with ID: {video_id}")
        video = Video.get_by_id(video_id)
        current_firebase_uid = get_current_firebase_uid()
        
        if not video:
            return jsonify({
                'error': 'Video not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this video
        if video.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'video': video.to_dict(include_user=include_user),
            'status': 'success'
        }), 200
            
    except Exception as e:
        logging.error(f"Error getting video: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@video_bp.route('/videos/my-videos', methods=['GET'])
@require_auth
def get_my_videos():
    """Get current user's videos"""
    try:
        firebase_uid = get_current_firebase_uid()
        
        # Check if user exists in our database
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({
                'error': 'User not registered. Please register first.',
                'status': 'error'
            }), 404
        
        videos = Video.get_by_firebase_uid(firebase_uid)
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'videos': [video.to_dict(include_user=include_user) for video in videos],
            'count': len(videos),
            'firebase_uid': firebase_uid,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting user videos: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@video_bp.route('/videos', methods=['GET'])
@require_auth
def get_all_videos():
    """Get all videos (admin only - for now returns user's videos)"""
    try:
        # For now, return only current user's videos
        # TODO: Add admin role check to return all videos
        firebase_uid = get_current_firebase_uid()
        
        videos = Video.get_by_firebase_uid(firebase_uid)
        
        # Check if user info should be included
        include_user = request.args.get('include_user', 'false').lower() == 'true'
        
        return jsonify({
            'videos': [video.to_dict(include_user=include_user) for video in videos],
            'count': len(videos),
            'status': 'success'
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting all videos: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@video_bp.route('/videos/<int:video_id>', methods=['PUT'])
@require_auth
def update_video(video_id):
    """Update video by ID"""
    try:
        data = request.get_json()
        current_firebase_uid = get_current_firebase_uid()
        
        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'status': 'error'
            }), 400
        
        # Get existing video
        video = Video.get_by_id(video_id)
        if not video:
            return jsonify({
                'error': 'Video not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this video
        if video.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        # Update fields if provided
        if 'videos_link' in data and data['videos_link']:
            videos_link = data['videos_link'].strip()
            if not validate_gcs_url(videos_link):
                return jsonify({
                    'error': 'Invalid Google Cloud Storage URL format',
                    'status': 'error'
                }), 400
            video.videos_link = videos_link
        
        # Save updated video
        result = video.update()
        
        if result['success']:
            return jsonify({
                'message': 'Video updated successfully',
                'video': video.to_dict(),
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to update video: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating video: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500

@video_bp.route('/videos/<int:video_id>', methods=['DELETE'])
@require_auth
def delete_video(video_id):
    """Delete video by ID"""
    try:
        current_firebase_uid = get_current_firebase_uid()
        
        # Get existing video
        video = Video.get_by_id(video_id)
        if not video:
            return jsonify({
                'error': 'Video not found',
                'status': 'error'
            }), 404
        
        # Check if user owns this video
        if video.firebase_uid != current_firebase_uid:
            return jsonify({
                'error': 'Access denied',
                'status': 'error'
            }), 403
        
        result = Video.delete_by_id(video_id)
        
        if result['success']:
            return jsonify({
                'message': 'Video deleted successfully',
                'status': 'success'
            }), 200
        else:
            return jsonify({
                'error': f'Failed to delete video: {result.get("error", "Unknown error")}',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logging.error(f"Error deleting video: {str(e)}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'error'
        }), 500
"""
Video model for TikTalk API Service
"""

from services.database_service import db_service
import logging

class Video:
    def __init__(self, id=None, firebase_uid=None, videos_link=None, user=None):
        self.id = id
        self.firebase_uid = firebase_uid  # Foreign key reference to users.firebase_uid
        self.videos_link = videos_link
        self.user = user  # User instance (lazy loaded)
    
    @classmethod
    def create_table(cls):
        """Create the videos table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS videos (
            id SERIAL PRIMARY KEY,
            firebase_uid VARCHAR(128) NOT NULL,
            videos_link TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (firebase_uid) REFERENCES users(firebase_uid) ON DELETE CASCADE,
            CONSTRAINT fk_videos_user FOREIGN KEY (firebase_uid) REFERENCES users(firebase_uid)
        );
        """
        
        result = db_service.execute_query(create_table_query)
        if result['success']:
            logging.info("Videos table created successfully")
        else:
            logging.error(f"Failed to create videos table: {result['error']}")
        return result['success']
    
    def save(self):
        """Save video to database"""
        insert_query = """
        INSERT INTO videos (firebase_uid, videos_link)
        VALUES (%s, %s)
        RETURNING id
        """
        
        params = (self.firebase_uid, self.videos_link)
        result = db_service.execute_query(insert_query, params, fetch_one=True)
        
        if result['success'] and result['data']:
            self.id = result['data']['id']
            logging.info(f"Video saved successfully with ID: {self.id}")
        else:
            logging.error(f"Failed to save video: {result.get('error', 'Unknown error')}")
        
        return result
    
    @classmethod
    def get_by_id(cls, video_id):
        """Get video by ID"""
        query = "SELECT * FROM videos WHERE id = %s"
        result = db_service.execute_query(query, (video_id,), fetch_one=True)
        
        if result['success'] and result['data']:
            video_data = result['data']
            return cls(
                id=video_data['id'],
                firebase_uid=video_data['firebase_uid'],
                videos_link=video_data['videos_link']
            )
        return None
    
    @classmethod
    def get_by_firebase_uid(cls, firebase_uid):
        """Get all videos by Firebase UID"""
        query = "SELECT * FROM videos WHERE firebase_uid = %s ORDER BY created_at DESC"
        result = db_service.execute_query(query, (firebase_uid,), fetch_all=True)
        
        if result['success']:
            videos = []
            for video_data in result['data']:
                videos.append(cls(
                    id=video_data['id'],
                    firebase_uid=video_data['firebase_uid'],
                    videos_link=video_data['videos_link']
                ))
            return videos
        return []
    
    @classmethod
    def get_all(cls):
        """Get all videos"""
        query = "SELECT * FROM videos ORDER BY created_at DESC"
        result = db_service.execute_query(query, fetch_all=True)
        
        if result['success']:
            videos = []
            for video_data in result['data']:
                videos.append(cls(
                    id=video_data['id'],
                    firebase_uid=video_data['firebase_uid'],
                    videos_link=video_data['videos_link']
                ))
            return videos
        return []
    
    def update(self):
        """Update video in database"""
        update_query = """
        UPDATE videos 
        SET videos_link = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        params = (self.videos_link, self.id)
        result = db_service.execute_query(update_query, params)
        
        if result['success']:
            logging.info(f"Video {self.id} updated successfully")
        else:
            logging.error(f"Failed to update video {self.id}: {result.get('error', 'Unknown error')}")
        
        return result
    
    @classmethod
    def delete_by_id(cls, video_id):
        """Delete video by ID"""
        delete_query = "DELETE FROM videos WHERE id = %s"
        result = db_service.execute_query(delete_query, (video_id,))
        
        if result['success']:
            logging.info(f"Video {video_id} deleted successfully")
        else:
            logging.error(f"Failed to delete video {video_id}: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_user(self):
        """Get the user instance for this video"""
        if not self.user and self.firebase_uid:
            from models.user import User
            self.user = User.get_by_firebase_uid(self.firebase_uid)
        return self.user
    
    def to_dict(self, include_user=False):
        """Convert video to dictionary"""
        result = {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'videos_link': self.videos_link
        }
        
        if include_user:
            user = self.get_user()
            if user:
                result['user'] = user.to_dict()
        
        return result
    
    def __repr__(self):
        return f"Video(id={self.id}, firebase_uid='{self.firebase_uid}', videos_link='{self.videos_link}')"

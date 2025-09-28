"""
Notes model for TikTalk API Service
"""

from services.database_service import db_service
import logging
from enum import Enum

class NotesStatus(Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    SCRIPTED = "scripted"
    AUDIO_GENERATED = "audio_generated"
    VIDEO_GENERATED = "video_generated"
    COMPLETED = "completed"

class Notes:
    def __init__(self, id=None, firebase_uid=None, title=None, notes_link=None, videos_link=None, status=NotesStatus.NOT_STARTED, user=None, created_at=None):
        self.id = id
        self.firebase_uid = firebase_uid
        self.title = title
        self.notes_link = notes_link
        self.videos_link = videos_link
        self.status = status.value if isinstance(status, NotesStatus) else status
        self.user = user
        self.created_at = created_at
    
    @classmethod
    def create_table(cls):
        """Create the notes table if it doesn't exist"""
        # Check if table exists first
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'notes'
        );
        """
        
        check_result = db_service.execute_query(check_table_query, fetch_one=True)
        if check_result['success'] and check_result['data'] and check_result['data']['exists']:
            logging.info("Notes table already exists, skipping creation")
            return True
        
        # Create the table with correct schema
        create_table_query = """
        CREATE TABLE notes (
            id SERIAL PRIMARY KEY,
            firebase_uid VARCHAR(128) NOT NULL,
            notes_link TEXT NOT NULL,
            videos_link TEXT DEFAULT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (status IN ('not_started', 'started', 'scripted', 'audio_generated', 'video_generated', 'completed'))
        );
        """
        
        result = db_service.execute_query(create_table_query)
        if result['success']:
            logging.info("Notes table created successfully")
        else:
            logging.error(f"Failed to create notes table: {result['error']}")
        return result['success']
    
    @classmethod
    def recreate_table(cls):
        """Force recreate the notes table (drops existing data)"""
        # First drop the table if it exists
        drop_table_query = "DROP TABLE IF EXISTS notes CASCADE;"
        drop_result = db_service.execute_query(drop_table_query)
        if drop_result['success']:
            logging.info("Notes table dropped successfully")
        else:
            logging.warning(f"Failed to drop notes table (may not exist): {drop_result['error']}")
        
        # Create the table with correct schema
        create_table_query = """
        CREATE TABLE notes (
            id SERIAL PRIMARY KEY,
            firebase_uid VARCHAR(128) NOT NULL,
            notes_link TEXT NOT NULL,
            videos_link TEXT DEFAULT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (status IN ('not_started', 'started', 'scripted', 'audio_generated', 'video_generated', 'completed'))
        );
        """
        
        result = db_service.execute_query(create_table_query)
        if result['success']:
            logging.info("Notes table recreated successfully")
        else:
            logging.error(f"Failed to recreate notes table: {result['error']}")
        return result['success']
    
    def save(self):
        """Save notes to database"""
        insert_query = """
        INSERT INTO notes (firebase_uid, title, notes_link, videos_link, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (self.firebase_uid, self.title, self.notes_link, self.videos_link or None, self.status)
        result = db_service.execute_query(insert_query, params, fetch_one=True)
        
        if result['success'] and result['data']:
            self.id = result['data']['id']
            logging.info(f"Notes saved successfully with ID: {self.id}")
        else:
            logging.error(f"Failed to save notes: {result.get('error', 'Unknown error')}")
        
        return result
    
    @classmethod
    def get_by_id(cls, notes_id):
        """Get notes by ID"""
        query = "SELECT * FROM notes WHERE id = %s"
        result = db_service.execute_query(query, (notes_id,), fetch_one=True)
        
        if result['success'] and result['data']:
            notes_data = result['data']
            return cls(
                id=notes_data['id'],
                firebase_uid=notes_data['firebase_uid'],
                title=notes_data['title'],
                notes_link=notes_data['notes_link'],
                videos_link=notes_data['videos_link'],
                status=notes_data['status'],
                created_at=notes_data.get('created_at')
            )
        return None
    
    @classmethod
    def get_by_firebase_uid(cls, firebase_uid):
        """Get all notes by Firebase UID"""
        query = "SELECT * FROM notes WHERE firebase_uid = %s ORDER BY created_at DESC"
        result = db_service.execute_query(query, (firebase_uid,), fetch_all=True)
        
        if result['success']:
            notes = []
            for notes_data in result['data']:
                notes.append(cls(
                    id=notes_data['id'],
                    firebase_uid=notes_data['firebase_uid'],
                    title=notes_data['title'],
                    notes_link=notes_data['notes_link'],
                    videos_link=notes_data['videos_link'],
                    status=notes_data['status'],
                    created_at=notes_data.get('created_at')
                ))
            return notes
        return []
    
    @classmethod
    def get_by_status(cls, status):
        """Get all notes by status"""
        query = "SELECT * FROM notes WHERE status = %s ORDER BY created_at DESC"
        result = db_service.execute_query(query, (status,), fetch_all=True)
        
        if result['success']:
            notes = []
            for notes_data in result['data']:
                notes.append(cls(
                    id=notes_data['id'],
                    firebase_uid=notes_data['firebase_uid'],
                    title=notes_data['title'],
                    notes_link=notes_data['notes_link'],
                    videos_link=notes_data['videos_link'],
                    status=notes_data['status'],
                    created_at=notes_data.get('created_at')
                ))
            return notes
        return []
    
    @classmethod
    def get_all(cls):
        """Get all notes"""
        query = "SELECT * FROM notes ORDER BY created_at DESC"
        result = db_service.execute_query(query, fetch_all=True)
        
        if result['success']:
            notes = []
            for notes_data in result['data']:
                notes.append(cls(
                    id=notes_data['id'],
                    firebase_uid=notes_data['firebase_uid'],
                    title=notes_data['title'],
                    notes_link=notes_data['notes_link'],
                    videos_link=notes_data['videos_link'],
                    status=notes_data['status'],
                    created_at=notes_data.get('created_at')
                ))
            return notes
        return []
    
    def update(self):
        """Update notes in database"""
        update_query = """
        UPDATE notes 
        SET title = %s, notes_link = %s, videos_link = %s, status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        params = (self.title, self.notes_link, self.videos_link, self.status, self.id)
        result = db_service.execute_query(update_query, params)
        
        if result['success']:
            logging.info(f"Notes {self.id} updated successfully")
        else:
            logging.error(f"Failed to update notes {self.id}: {result.get('error', 'Unknown error')}")
        
        return result
    
    def update_status(self, new_status):
        """Update only the status of notes"""
        if isinstance(new_status, NotesStatus):
            new_status = new_status.value
        
        update_query = """
        UPDATE notes 
        SET status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        params = (new_status, self.id)
        result = db_service.execute_query(update_query, params)
        
        if result['success']:
            self.status = new_status
            logging.info(f"Notes {self.id} status updated to {new_status}")
        else:
            logging.error(f"Failed to update notes {self.id} status: {result.get('error', 'Unknown error')}")
        
        return result
    
    @classmethod
    def delete_by_id(cls, notes_id):
        """Delete notes by ID"""
        delete_query = "DELETE FROM notes WHERE id = %s"
        result = db_service.execute_query(delete_query, (notes_id,))
        
        if result['success']:
            logging.info(f"Notes {notes_id} deleted successfully")
        else:
            logging.error(f"Failed to delete notes {notes_id}: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_user(self):
        """Get the user instance for this notes"""
        if not self.user and self.firebase_uid:
            from models.user import User
            self.user = User.get_by_firebase_uid(self.firebase_uid)
        return self.user
    
    def to_dict(self, include_user=False):
        """Convert notes to dictionary"""
        result = {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'title': self.title,
            'notes_link': self.notes_link,
            'videos_link': self.videos_link,
            'status': self.status,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }
        
        if include_user:
            user = self.get_user()
            if user:
                result['user'] = user.to_dict()
        
        return result
    
    def __repr__(self):
        return f"Notes(id={self.id}, firebase_uid='{self.firebase_uid}', notes_link='{self.notes_link}', status='{self.status}')"

"""
User model for TikTalk API Service with Firebase integration
"""

from services.database_service import db_service
import logging

class User:
    def __init__(self, firebase_uid, email, full_name, username=None):
        self.firebase_uid = firebase_uid  # Primary key - Firebase UID
        self.email = email
        self.full_name = full_name
        self.username = username  # Optional display name
    
    @classmethod
    def create_table(cls):
        """Create the users table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            firebase_uid VARCHAR(128) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            username VARCHAR(50) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        result = db_service.execute_query(create_table_query)
        if result['success']:
            logging.info("Users table created successfully")
        else:
            logging.error(f"Failed to create users table: {result['error']}")
        return result['success']
    
    def save(self):
        """Save user to database"""
        insert_query = """
        INSERT INTO users (firebase_uid, email, full_name, username)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (firebase_uid) DO UPDATE SET
            email = EXCLUDED.email,
            full_name = EXCLUDED.full_name,
            username = EXCLUDED.username,
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = (self.firebase_uid, self.email, self.full_name, self.username)
        result = db_service.execute_query(insert_query, params)
        
        if result['success']:
            logging.info(f"User {self.firebase_uid} saved successfully")
        else:
            logging.error(f"Failed to save user {self.firebase_uid}: {result['error']}")
        
        return result
    
    @classmethod
    def get_by_firebase_uid(cls, firebase_uid):
        """Get user by Firebase UID"""
        query = "SELECT * FROM users WHERE firebase_uid = %s"
        result = db_service.execute_query(query, (firebase_uid,), fetch_one=True)
        
        if result['success'] and result['data']:
            user_data = result['data']
            return cls(
                firebase_uid=user_data['firebase_uid'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                username=user_data['username']
            )
        return None
    
    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = %s"
        result = db_service.execute_query(query, (username,), fetch_one=True)
        
        if result['success'] and result['data']:
            user_data = result['data']
            return cls(
                firebase_uid=user_data['firebase_uid'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                username=user_data['username']
            )
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = db_service.execute_query(query, (email,), fetch_one=True)
        
        if result['success'] and result['data']:
            user_data = result['data']
            return cls(
                firebase_uid=user_data['firebase_uid'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                username=user_data['username']
            )
        return None
    
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'firebase_uid': self.firebase_uid,
            'email': self.email,
            'full_name': self.full_name,
            'username': self.username
        }
    
    def __repr__(self):
        return f"User(firebase_uid='{self.firebase_uid}', email='{self.email}', full_name='{self.full_name}', username='{self.username}')"

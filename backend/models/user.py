"""
User model for TikTalk API Service
"""

from services.database_service import db_service
import logging

class User:
    def __init__(self, username, email, full_name):
        self.username = username
        self.email = email
        self.full_name = full_name
    
    @classmethod
    def create_table(cls):
        """Create the users table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
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
        INSERT INTO users (username, email, full_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO UPDATE SET
            email = EXCLUDED.email,
            full_name = EXCLUDED.full_name,
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = (self.username, self.email, self.full_name)
        result = db_service.execute_query(insert_query, params)
        
        if result['success']:
            logging.info(f"User {self.username} saved successfully")
        else:
            logging.error(f"Failed to save user {self.username}: {result['error']}")
        
        return result
    
    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = %s"
        result = db_service.execute_query(query, (username,), fetch_one=True)
        
        if result['success'] and result['data']:
            user_data = result['data']
            return cls(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name']
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
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name']
            )
        return None
    
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name
        }
    
    def __repr__(self):
        return f"User(username='{self.username}', email='{self.email}', full_name='{self.full_name}')"

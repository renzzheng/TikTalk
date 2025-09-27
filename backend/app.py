from flask import Flask
from dotenv import load_dotenv
import logging

from services.database_service import db_service
from routes.file_processing import file_processing_bp
from routes.user_routes import user_bp
from routes.video_routes import video_bp
from routes.notes_routes import notes_bp
from models.user import User
from models.video import Video
from models.notes import Notes
from confluent_kafka import Producer
from flask_cors import CORS


# Firebase service
from services.firebase_auth import initialize_firebase

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)


    # Initialize Firebase Admin SDK (for auth)
    initialize_firebase()

    # Kafka producer (if you really need it)
    producer = Producer({'bootstrap.servers': 'localhost:9092'})

    # Register blueprints
    app.register_blueprint(file_processing_bp, url_prefix='/api/files')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(video_bp, url_prefix='/api')
    app.register_blueprint(notes_bp, url_prefix='/api')
    
    # Initialize database tables
    User.create_table()
    Video.create_table()
    Notes.create_table()

    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        db_status = db_service.test_connection()
        firebase_status = initialize_firebase()

        return {
            "status": "healthy" if db_status and firebase_status else "degraded",
            "services": {
                "rds": "connected" if db_status else "disconnected",
                "firebase": "initialized" if firebase_status else "not initialized"
            }
        }
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)

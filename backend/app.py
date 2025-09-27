from flask import Flask
from dotenv import load_dotenv
import os
from services.database_service import db_service
from routes.file_processing import file_processing_bp
from routes.user_routes import user_bp
from routes.video_routes import video_bp
from routes.notes_routes import notes_bp
from models.user import User
from models.video import Video
from models.notes import Notes
from confluent_kafka import Producer
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GCLOUD_PROJECT = os.getenv("GCLOUD_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def create_app():
    app = Flask(__name__)
    producer = Producer({'bootstrap.servers': 'localhost:9092'})

    gcs_client = storage.Client.from_service_account_json(
        GOOGLE_APPLICATION_CREDENTIALS, project=GCLOUD_PROJECT
    )
    bucket = gcs_client.bucket(BUCKET_NAME)

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

        try:
            blobs = list(bucket.list_blobs(max_results=1))
            gcs_status = True if blobs is not None else False
        except GoogleAPIError:
            gcs_status = False

        return {
            "status": "healthy" if db_status and gcs_status else "degraded",
            "services": {
                "rds": "connected" if db_status else "disconnected",
                "gcs": "connected" if gcs_status else "disconnected"
            }
        }
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
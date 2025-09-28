from flask import Blueprint, request, jsonify
from confluent_kafka import Producer
import json
import time
import uuid
from dotenv import load_dotenv
import os
from urllib.parse import unquote

from models.notes import Notes, NotesStatus
from services.firebase_auth import require_auth, get_current_firebase_uid
from models.user import User

file_processing_bp = Blueprint('file_processing', __name__)
load_dotenv()

# Google Cloud Storage config
GCLOUD_PROJECT = os.getenv("GCLOUD_PROJECT")
GCS_CREDENTIALS = os.getenv("GCS_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Kafka producer configuration
def get_kafka_producer():
    return Producer({'bootstrap.servers': 'localhost:9092'})


@file_processing_bp.route('/process-files', methods=['POST'])
@require_auth
def process_multiple_files():
    """
    Accepts list of file URLs (PDFs, audio, video), normalizes them,
    creates a Notes entry in DB (notes_link = folder prefix),
    and pushes a single message with all URLs to Kafka for async processing.
    Requires Firebase authentication.
    """
    try:
        data = request.get_json()

        if not data or 'file_urls' not in data or not isinstance(data['file_urls'], list):
            return jsonify({
                'error': 'Missing or invalid file_urls (expected list)',
                'status': 'error'
            }), 400

        raw_urls = data['file_urls']
        normalized_urls = []

        for raw_url in raw_urls:
            decoded_url = unquote(raw_url)

            # Normalize → always HTTPS
            if decoded_url.startswith("gs://"):
                parts = decoded_url.replace("gs://", "").split("/", 1)
                if len(parts) != 2:
                    return jsonify({
                        "error": f"Invalid GCS URL: {decoded_url}"
                    }), 400
                bucket, key = parts
                gcs_url = f"https://storage.googleapis.com/{bucket}/{key}"
            elif "storage.googleapis.com" in decoded_url:
                gcs_url = decoded_url
            else:
                return jsonify({
                    "error": f"Invalid URL format: {decoded_url}"
                }), 400

            normalized_urls.append(gcs_url)

        firebase_uid = get_current_firebase_uid()
        user = User.get_by_firebase_uid(firebase_uid)
        if not user:
            return jsonify({
                "error": "User not registered. Please register first.",
                "status": "error"
            }), 404

        unique_id = str(uuid.uuid4())
        notes_folder = f"notes/{firebase_uid}/{unique_id}/"
        notes_link = f"https://storage.googleapis.com/{BUCKET_NAME}/{notes_folder}"

        notes = Notes(
            firebase_uid=firebase_uid,
            notes_link=notes_link,
            status=NotesStatus.NOT_STARTED
        )
        save_result = notes.save()
        if not save_result['success']:
            return jsonify({
                "error": f"Failed to create notes entry: {save_result.get('error', 'Unknown error')}",
                "status": "error",
            }), 500

        # Kafka message payload
        message = {
            "notes_id": notes.id,
            "firebase_uid": firebase_uid,
            "file_urls": normalized_urls,
            "notes_link": notes_link,
            "bucket": BUCKET_NAME,
            "project": GCLOUD_PROJECT,
            "timestamp": str(time.time()),
            "status": "pending",
        }

        producer = get_kafka_producer()
        producer.produce(
            "pdf-processing",
            value=json.dumps(message).encode("utf-8"),
            callback=lambda err, msg: (
                print(f"Message delivered: {msg}")
                if err is None
                else print(f"Message delivery failed: {err}")
            ),
        )
        producer.flush()

        results = [{"pdf_url": url, "status": "accepted"} for url in normalized_urls]

        return jsonify({
            "message": "PDF processing request accepted",
            "notes": notes.to_dict(),
            "results": results,
            "status": "accepted",
        }), 202

    except Exception as e:
        return jsonify({
            "error": f"Failed to process multiple PDFs: {str(e)}",
            "status": "error",
        }), 500

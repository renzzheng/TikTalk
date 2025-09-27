from flask import Blueprint, request, jsonify
from confluent_kafka import Producer
import json
import time

from dotenv import load_dotenv
import os
from urllib.parse import urlparse, unquote
file_processing_bp = Blueprint('file_processing', __name__)



load_dotenv()

# Google Cloud Storage config
GCLOUD_PROJECT = os.getenv("GCLOUD_PROJECT")
GCS_CREDENTIALS = os.getenv("GCS_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")


# Kafka producer configuration
def get_kafka_producer():
    return Producer({'bootstrap.servers': 'localhost:9092'})

@file_processing_bp.route('/process-pdf', methods=['POST'])
def process_pdf():
    """
    API endpoint to process a single PDF from Google Cloud Storage bucket
    Accepts a PDF URL and sends it to Kafka for async processing
    """
    try:
        data = request.get_json()
        
        if not data or 'pdf_url' not in data:
            return jsonify({
                'error': 'Missing pdf_url in request body',
                'status': 'error'
            }), 400
        
        pdf_url = data['pdf_url']
        
        # Validate that it's a Google Cloud Storage URL
        if not pdf_url.startswith('gs://') and 'storage.googleapis.com' not in pdf_url:
            return jsonify({
                'error': 'Invalid Google Cloud Storage URL format',
                'status': 'error'
            }), 400
        
        producer = get_kafka_producer()
        message = {
            'pdf_url': pdf_url,
            'timestamp': str(time.time()),
            'status': 'pending'
        }
        
        producer.produce(
            'pdf-processing',
            value=json.dumps(message).encode('utf-8'),
            callback=lambda err, msg: print(f'Message delivered: {msg}') if err is None else print(f'Message delivery failed: {err}')
        )
        producer.flush()
        
        return jsonify({
            'message': 'PDF processing request submitted successfully',
            'pdf_url': pdf_url,
            'status': 'accepted',
            'processing_id': message['timestamp']
        }), 202
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to process PDF request: {str(e)}',
            'status': 'error'
        }), 500


@file_processing_bp.route('/process-pdf2', methods=['POST'])
def process_multiple_pdfs():
    """
    Accepts list of PDF URLs, normalizes them,
    and pushes messages to Kafka for async processing.
    """
    try:
        data = request.get_json()

        if not data or 'pdf_urls' not in data or not isinstance(data['pdf_urls'], list):
            return jsonify({
                'error': 'Missing or invalid pdf_urls (expected list)',
                'status': 'error'
            }), 400

        pdf_urls = data['pdf_urls']
        producer = get_kafka_producer()
        results = []

        for raw_url in pdf_urls:
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

            message = {
                "pdf_url": gcs_url,   # ✅ always HTTPS
                "original_url": raw_url,
                "bucket": BUCKET_NAME,
                "project": GCLOUD_PROJECT,
                "timestamp": str(time.time()),
                "status": "pending",
            }

            producer.produce(
                "pdf-processing",
                value=json.dumps(message).encode("utf-8"),
                callback=lambda err, msg: (
                    print(f"Message delivered: {msg}")
                    if err is None
                    else print(f"Message delivery failed: {err}")
                ),
            )

            results.append({
                "pdf_url": gcs_url,
                "processing_id": message["timestamp"],
                "status": "accepted",
            })

        producer.flush()

        return jsonify({
            "message": "Multiple PDF processing requests submitted successfully",
            "results": results,
            "status": "accepted",
        }), 202

    except Exception as e:
        return jsonify({
            "error": f"Failed to process multiple PDFs: {str(e)}",
            "status": "error",
        }), 500

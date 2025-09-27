from flask import Blueprint, request, jsonify
from confluent_kafka import Producer
import json
import os
import time

file_processing_bp = Blueprint('file_processing', __name__)

# Kafka producer configuration
def get_kafka_producer():
    return Producer({'bootstrap.servers': 'localhost:9092'})

@file_processing_bp.route('/process-pdf', methods=['POST'])
def process_pdf():
    """
    API endpoint to process PDF from Google Cloud Storage bucket
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
        
        # Create Kafka producer
        producer = get_kafka_producer()
        
        # Prepare message for Kafka
        message = {
            'pdf_url': pdf_url,
            'timestamp': str(time.time()),
            'status': 'pending'
        }
        
        # Send message to Kafka topic
        topic = 'pdf-processing'
        producer.produce(
            topic,
            value=json.dumps(message).encode('utf-8'),
            callback=lambda err, msg: print(f'Message delivered: {msg}') if err is None else print(f'Message delivery failed: {err}')
        )
        
        # Flush to ensure message is sent
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

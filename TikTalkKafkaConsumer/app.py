#!/usr/bin/env python3
"""
TikTalk Kafka Consumer
Consumes messages from Kafka topics and processes them asynchronously
"""

from confluent_kafka import Consumer, KafkaError
import json
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TikTalkKafkaConsumer:
    def __init__(self):
        """Initialize the Kafka consumer"""
        self.consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'tiktalk-consumer-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 1000
        })
        
        self.topics = ['pdf-processing']
        self.consumer.subscribe(self.topics)
        
        logger.info(f"Consumer initialized and subscribed to topics: {self.topics}")
    
    def process_pdf_message(self, message_data):
        """
        Process PDF processing message
        For now, just prints 'hi' and the Google Cloud bucket link as requested
        """
        try:
            pdf_url = message_data.get('pdf_url', 'Unknown URL')
            timestamp = message_data.get('timestamp', 'Unknown timestamp')
            status = message_data.get('status', 'Unknown status')
            
            logger.info("=" * 50)
            logger.info("PDF PROCESSING ACTIVATED!")
            logger.info("hi") 
            logger.info(f"Google Cloud Bucket PDF URL: {pdf_url}")
            logger.info(f"Processing timestamp: {timestamp}")
            logger.info(f"Status: {status}")
            logger.info("=" * 50)
            
            # Here you would add actual PDF processing logic
            # For example:
            # - Download PDF from GCS
            # - Extract text using PyPDF2 or pdfplumber
            # - Process with OCR if needed
            # - Store results in database
            # - Send notifications, etc.
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing PDF message: {str(e)}")
            return False
    
    def process_message(self, message):
        """Process incoming Kafka message"""
        try:
            # Decode message
            message_data = json.loads(message.value().decode('utf-8'))
            topic = message.topic()
            
            logger.info(f"Received message from topic '{topic}': {message_data}")
            
            # Route message based on topic
            if topic == 'pdf-processing':
                success = self.process_pdf_message(message_data)
                if success:
                    logger.info("PDF processing completed successfully")
                else:
                    logger.error("PDF processing failed")
            else:
                logger.warning(f"Unknown topic: {topic}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def run(self):
        """Main consumer loop"""
        logger.info("Starting TikTalk Kafka Consumer...")
        
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                else:
                    # Process the message
                    self.process_message(msg)
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")
        finally:
            self.consumer.close()
            logger.info("Consumer closed")

def main():
    """Main entry point"""
    try:
        consumer = TikTalkKafkaConsumer()
        consumer.run()
    except Exception as e:
        logger.error(f"Failed to start consumer: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
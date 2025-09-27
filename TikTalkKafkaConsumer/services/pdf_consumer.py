"""
Kafka Consumer for TikTalk
Consumes messages with PDF URLs, extracts text (pdfplumber + pytesseract),
and logs lecture notes.
"""

import json
import io
import logging
import requests
import pdfplumber
from PIL import Image
import pytesseract
from confluent_kafka import Consumer, KafkaError

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: io.BytesIO) -> str:
    """Extract text using pdfplumber, fallback to pytesseract for images."""
    extracted_text = []

    with pdfplumber.open(pdf_bytes) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""

            if not page_text.strip():
                pil_image = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(pil_image)
                page_text = ocr_text or ""

            extracted_text.append(page_text)

    return "\n".join(extracted_text)


class TikTalkKafkaConsumer:
    def __init__(self):
        """Initialize Kafka consumer"""
        self.consumer = Consumer(
            {
                "bootstrap.servers": "localhost:9092",
                "group.id": "tiktalk-consumer-group",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
            }
        )
        self.topics = ["pdf-processing"]
        self.consumer.subscribe(self.topics)
        logger.info(f"Subscribed to topics: {self.topics}")

    def process_pdf_message(self, message_data: dict) -> bool:
        try:
            pdf_url = message_data.get("pdf_url")
            if not pdf_url:
                logger.error("No pdf_url in message")
                return False

            logger.info("=" * 50)
            logger.info(f"Processing PDF: {pdf_url}")

            # Download PDF
            response = requests.get(pdf_url)
            if response.status_code != 200:
                logger.error(f"Failed to download PDF: {response.status_code}")
                return False

            pdf_bytes = io.BytesIO(response.content)
            full_text = extract_text_from_pdf(pdf_bytes)

            logger.info("--- LECTURE PREVIEW (first 1000 chars) ---")
            logger.info(full_text[:1000])
            logger.info("=" * 50)
            return True


            # TODO, use google Gemini API to generate lecture scripts

            # TODO, use text to speech to generate audio files and upload to google cloud bucket

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return False

    def process_message(self, message):
        try:
            message_data = json.loads(message.value().decode("utf-8"))
            topic = message.topic()
            logger.info(f"Received message on {topic}: {message_data}")

            if topic == "pdf-processing":
                self.process_pdf_message(message_data)
            else:
                logger.warning(f"Unknown topic: {topic}")

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    def run(self):
        logger.info("Starting TikTalk Kafka Consumer...")
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Consumer error: {msg.error()}")
                else:
                    self.process_message(msg)
        finally:
            self.consumer.close()
            logger.info("Consumer closed")

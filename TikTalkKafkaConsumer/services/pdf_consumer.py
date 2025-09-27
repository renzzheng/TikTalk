"""
Kafka Consumer for TikTalk
Consumes messages with PDF URLs, extracts text (pdfplumber + pytesseract),
and logs lecture notes.
"""

from flask import Flask, request, jsonify, send_file
import json
import io
import logging
import requests
import pdfplumber
from PIL import Image
import pytesseract
from confluent_kafka import Consumer, KafkaError

import os
from google.cloud import texttospeech, generativelanguage
from google import genai

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

# (1) create script using google cloud genai
def script():
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY")) # replace with real key

        prompt = (
            "Based on this text, can you give me a small script for a short 30 second TikTok video?Return to me only the plain transcript, with only the narration to the video, and do not include any sound cues. I need you to personally shut up and not say anything. As for the content of the script, can you use the text to explain concisely, but with some level of depth so that it is not too brief, on the topics in the text that is being read? It should be detailed enough to teach the viewer information that is not simply superficial level knowledge. Give it a nice hook and ending transition that would be fit for a TikTok style video. Do not ask the watcher to subscribe, like, comment, or anything like that at the end."
        )
        response = client.responses.create(
            model="models/gemini-2.5-flash", # is this the correct model?
            input=prompt
        )

        return jsonify(response.to_dict())

# (2) use google cloud tts to create audio
def audio():
    tts_client = 


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
            script()

            # TODO, use text to speech to generate audio files and upload to google cloud bucket
            audio()

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

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
from google import genai
from google.cloud import texttospeech, storage

from dotenv import load_dotenv
load_dotenv()

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

    # (1) create script using google cloud genai
    def script(self, text: str) -> str:
        # Get API key
        api_key = os.environ.get("GEMINI_API_KEY")
        print(api_key)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Create the GenAI client with API key
        client = genai.Client(api_key=api_key)
        print("GenAI client created:", client)

        prompt = (
            f"Based on this text: {text}, can you give me a small script for a short 30 second TikTok video?Return to me only the plain transcript, with only the narration to the video, and do not include any sound cues. I need you to personally shut up and not say anything. As for the content of the script, can you use the text to explain concisely, but with some level of depth so that it is not too brief, on the topics in the text that is being read? It should be detailed enough to teach the viewer information that is not simply superficial level knowledge. Give it a nice hook and ending transition that would be fit for a TikTok style video. Do not ask the watcher to subscribe, like, comment, or anything like that at the end."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash", # is this the correct model?
            contents=prompt
        )

        script_text = response.candidates[0].content.parts[0].text
        print(script_text)

        return script_text
    
    # (2) use google cloud tts to create audio
    def audio(self, text: str, output_filename="audio.mp3") -> str:
            client = texttospeech.TextToSpeechClient()
            # set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            # build voice request, select language code and the voice gender
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            # select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            # perform the tts request on the text input with the selected voice parameters and audio file type
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            # the response's audio_content is binary
            with open(output_filename, "wb") as out:
                # write the response to the output file.
                out.write(response.audio_content)
                print(f'Audio content written to file {output_filename}')

            return output_filename

    # (3) upload the object into the bucket
    def upload_blob(self, bucket_name, source_file_name, destination_blob_name):
        """Uploads a file to the bucket."""
        # The ID of your GCS bucket
        # bucket_name = "your-bucket-name"
        # The path to your file to upload
        # source_file_name = "local/path/to/file"
        # The ID of your GCS object
        # destination_blob_name = "storage-object-name"

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # delete existing object if it exists
        if blob.exists(): blob.delete()

        generation_match_precondition=0

        # upload to storage bucket
        blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

        print(
            f"File {source_file_name} uploaded to {destination_blob_name}."
        )

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

            # TODO, use google Gemini API to generate lecture scripts
            script = self.script(full_text)
            logger.info("--- GENERATED TIKTOK SCRIPT ---")
            logger.info(script)

            # TODO, use text to speech to generate audio files and upload to google cloud bucket
            audio_file_name = self.audio(script, "_audio.mp3")

            # TODO, upload mp3 file to google cloud storage bucket
            bucket_name = "tiktalk-bucket"
            source_file_name=audio_file_name
            destination_blob_name = "outputs/audio.mp3"
            self.upload_blob(bucket_name, source_file_name, destination_blob_name)

            return True

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

from flask import Flask, request, jsonify, send_file
import json
import io
import logging
import requests
import pdfplumber
from PIL import Image
import pytesseract
from confluent_kafka import Consumer, KafkaError
import openai

import os
from google import genai
from google.cloud import texttospeech, storage
from .status_updater import StatusUpdater
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import tempfile

from dotenv import load_dotenv
load_dotenv()

# Remove proxy environment variables that might interfere with OpenAI client
if "http_proxy" in os.environ:
    del os.environ["http_proxy"]
if "https_proxy" in os.environ:
    del os.environ["https_proxy"]

# Set OpenAI API key for the client
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

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
        self.status_updater = StatusUpdater()
        logger.info(f"Subscribed to topics: {self.topics}")

    # (0) Create script from mp4 using OpenAI Whisper
    def transcribe_vid(self, file_url: str) -> str:
        # Download the file
        response = requests.get(file_url)
        response.raise_for_status()

        # Determine file extension
        ext = os.path.splitext(file_url)[-1].lower()
        suffix = ext if ext in [".mp3", ".wav", ".m4a"] else ".mp3"

        # Save downloaded content to a temporary file
        with tempfile.NamedTemporaryFile(suffix=ext) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()

            # If the file is a video, extract audio first
            if ext in [".mp4", ".mov", ".mkv"]:
                try:
                    with tempfile.NamedTemporaryFile(suffix=".mp3") as audio_file:
                        # Convert video to audio using MoviePy
                        logger.info("Converting video to audio using MoviePy...")
                        video_clip = VideoFileClip(tmp_file.name)
                        audio_clip = video_clip.audio
                        audio_clip.write_audiofile(audio_file.name, verbose=False, logger=None)
                        
                        # Clean up video and audio clips
                        video_clip.close()
                        audio_clip.close()

                        # Transcribe audio using Whisper
                        logger.info("Transcribing audio with OpenAI Whisper...")
                        with open(audio_file.name, "rb") as f:
                            # Use the older API format for openai 0.28.1
                            transcript = openai.Audio.transcribe(
                                model="whisper-1",
                                file=f,
                                response_format="text"
                            )
                except Exception as e:
                    logger.error(f"Error processing video with MoviePy: {str(e)}")
                    # Fallback: try to transcribe the video file directly
                    logger.info("Attempting direct video transcription...")
                    with open(tmp_file.name, "rb") as f:
                        # Use the older API format for openai 0.28.1
                        transcript = openai.Audio.transcribe(
                            model="whisper-1",
                            file=f,
                            response_format="text"
                        )
            else:
                # Already audio: directly transcribe
                with open(tmp_file.name, "rb") as f:
                    # Use the older API format for openai 0.28.1
                    transcript = openai.Audio.transcribe(
                        model="whisper-1",
                        file=f,
                        response_format="text"
                    )

        # If response_format="text", OpenAI returns a string directly
        if isinstance(transcript, str):
            return transcript
        # Otherwise, access .text for older OpenAI versions
        return transcript.text

    def script(self, text: str) -> str:
        # get API key
        api_key = os.environ.get("GEMINI_API_KEY")
        print(api_key)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # create the GenAI client with API key
        client = genai.Client(api_key=api_key)

        prompt = (
            f"Based on this text: {text}\n"
            "Write a concise TikTok narration script split into paragraphs. "
            "Each paragraph should correspond to a separate topic"
            "Create less 10 video based on the information given less is usually better. maybe based on the topics and the texts that are there"
            "Do not make more than 10 videos. recommendation is 5-7 videos"
            "video should be approximately a 30-second narration. "
            "Return only the plain transcript text — no sound cues or extra commentary. "
            "Use the text to clearly explain the topic with depth, not just surface-level facts, so the viewer learns something new. "
            "Start with a strong hook, and finish with a smooth transition that connects naturally to the next subtopic. "
            "The tone should be engaging and easy to follow, suited for TikTok. "
            "Ensure each script paragraph feels slightly connected to the others for a seamless video series."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
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

    def create_video(self, background_video_url: str, audio_file: str, output_filename: str) -> str:
        """Create a video by combining background video with audio file."""
        try:
            # Download background video
            logger.info(f"Downloading background video from: {background_video_url}")
            response = requests.get(background_video_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download background video: {response.status_code}")
            
            # Save background video to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                temp_video.write(response.content)
                temp_video_path = temp_video.name
            
            # Load video and audio clips
            video_clip = VideoFileClip(temp_video_path)
            audio_clip = AudioFileClip(audio_file)
            
            # Get the duration of the audio
            audio_duration = audio_clip.duration
            
            # If video is longer than audio, trim it to match audio duration
            if video_clip.duration > audio_duration:
                video_clip = video_clip.subclip(0, audio_duration)
            # If video is shorter than audio, loop it to match audio duration
            elif video_clip.duration < audio_duration:
                loops_needed = int(audio_duration / video_clip.duration) + 1
                video_clip = video_clip.loop(loops_needed).subclip(0, audio_duration)
            
            # Set the audio of the video clip to the new audio
            final_video = video_clip.set_audio(audio_clip)
            
            # Write the result to file
            final_video.write_videofile(
                output_filename,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up
            video_clip.close()
            audio_clip.close()
            final_video.close()
            os.unlink(temp_video_path)
            
            logger.info(f"Video created successfully: {output_filename}")
            return output_filename
            
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            # Clean up temp file if it exists
            if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
                os.unlink(temp_video_path)
            raise e


    def process_pdf_message(self, message_data: dict) -> bool:
        try:
            # Get notes_id from message
            notes_id = message_data.get("notes_id")
            if not notes_id:
                logger.error("No notes_id in message")
                return False
            
            logger.info(f"Processing PDFs for notes_id: {notes_id}")
            
            # Mark as started immediately when processing begins
            if not self.status_updater.mark_as_started(notes_id):
                logger.error(f"Failed to mark notes {notes_id} as started")
                return False
            
            all_text = ""
            file_urls = message_data.get("file_urls")
            if not file_urls or not isinstance(file_urls, list):
                logger.error("No file_urls in message")
                return False

            for file_url in file_urls:
                logger.info("=" * 50)
                logger.info(f"Processing file: {file_url}")

                # Handle MP4 video first
                if file_url.endswith((".mp4", ".mp3", ".wav", ".m4a", ".mov", ".mkv")):
                    logger.info("Detected audio/video file, transcribing...")
                    all_text = self.transcribe_vid(file_url)
                    script = self.script(all_text)
                    print(script)
                    logger.info("All scripts loaded")
                elif file_url.endswith(".pdf"):
                    logger.info("Detected PDF, extracting text...")
                    # Download PDF
                    response = requests.get(file_url)
                    if response.status_code != 200:
                        logger.error(f"Failed to download PDF: {response.status_code}")
                        continue

                    pdf_bytes = io.BytesIO(response.content)
                    full_text = extract_text_from_pdf(pdf_bytes)
                    all_text = all_text + full_text
                    # Generate TikTok script from pdf text
                    script = self.script(all_text)
                    print(script)
                    logger.info("All scripts loaded")
                else:
                    logger.warning(f"Unsupported file type: {file_url}")
                    continue

            print(script)

            # Split script by paragraphs
            paragraphs = [p.strip() for p in script.split("\n") if p.strip()]

            # Loop through paragraphs and generate audio
            for i, para in enumerate(paragraphs, start=1):
                output_filename = f"output_{i}.mp3"
                self.audio(para, output_filename=output_filename)
                print(f"Audio generated: {output_filename}")

            # Create videos by combining background video with each audio file
            background_video_url = "https://storage.googleapis.com/tiktalk-bucket/background/Lunatic%20Genji%20Be%20Cuttin!.mp4"
            video_links = []
            
            for i in range(1, len(paragraphs) + 1):
                audio_file = f"output_{i}.mp3"
                video_file = f"video_{i}.mp4"
                
                if os.path.exists(audio_file):
                    try:
                        self.create_video(background_video_url, audio_file, video_file)
                        print(f"Video created: {video_file}")
                        
                        # Upload video to Google Cloud Storage
                        video_path = f"videos/{notes_id}/video_{i}.mp4"
                        self.upload_blob("tiktalk-bucket", video_file, video_path)
                        print(f"Video uploaded: {video_path}")
                        
                        # Add video link to the list
                        video_url = f"https://storage.googleapis.com/tiktalk-bucket/{video_path}"
                        video_links.append(video_url)
                        
                        # Delete local audio file after successful video creation and upload
                        os.remove(audio_file)
                        logger.info(f"Deleted local audio file: {audio_file}")
                        
                        # Keep video file locally (not deleted)
                        
                    except Exception as e:
                        logger.error(f"Error creating video {i}: {str(e)}")
                        # Clean up audio file even if video creation failed
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
                            logger.info(f"Cleaned up audio file after error: {audio_file}")
                else:
                    logger.warning(f"Audio file not found: {audio_file}")

            # Mark as completed when processing is done with actual video links
            video_links_str = ",".join(video_links) if video_links else None
            success = self.status_updater.mark_as_completed(notes_id, video_links_str)
            
            if success:
                logger.info(f"Successfully completed processing for notes {notes_id}")
            else:
                logger.error(f"Failed to mark notes {notes_id} as completed")
            

            return success

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return False

    def process_message(self, message):
        try:
            # set the note status to started
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

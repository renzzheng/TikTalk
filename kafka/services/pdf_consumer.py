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
import random
import signal
import threading
from google import genai
from google.cloud import texttospeech, storage
from .status_updater import StatusUpdater
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ColorClip, ImageClip
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
            "Make the below thing in one paragraph. I need you to repeat the phrase below: also, don't make it word for word, change up the wording of 'need to study want to watch tiktok' etc.\n\n"
            "Need to study? Want to watch TikTok though? Our attention spans are lowering according to  USC Dr. Albright's studies. As we head on, it becomes harder and harder to focus on boring content. In most cases, within minutes you'll be wondering: when will something happen? How do platforms like TikTok or Instagram prey on our shifting mindset?\n\n"
            "\"In psychological terms [it's] called random reinforcement,\" Dr. Albrixght says. \"It means sometimes you win, sometimes you lose. And that's how these platforms are designed... they're exactly like a slot machine. Well, the one thing we know is slot machines are addictive. But we don't often talk about how our devices and these platforms and these apps do have these same addictive qualities baked into them.\"\n\n"
            "With TikTalk, we take advantage of the ever-changing content of these videos. We combine the content of coursework, with the addictiveness of TikTok to produce short clips summarizing the most important content of the course. ."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        script_text = response.candidates[0].content.parts[0].text

        return script_text
    
    # (2) use google cloud tts to create audio
    def audio(self, text: str, output_filename="audio.mp3", voice_name=None) -> str:
            client = texttospeech.TextToSpeechClient()
            # set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Select voice - use provided voice or random one
            if voice_name:
                selected_voice = voice_name
            else:
                # Random voice selection
                voices = [
                    "en-US-Wavenet-A",  # Male, American
                    "en-US-Wavenet-B",  # Male, American
                    "en-US-Wavenet-C",  # Female, American
                    "en-US-Wavenet-D",  # Male, American
                    "en-US-Wavenet-E",  # Female, American
                    "en-US-Wavenet-F",  # Female, American
                    "en-US-Standard-A", # Male, American
                    "en-US-Standard-B", # Male, American
                    "en-US-Standard-C", # Female, American
                    "en-US-Standard-D", # Male, American
                    "en-US-Standard-E", # Female, American
                    "en-US-Standard-F", # Female, American
                ]
                selected_voice = random.choice(voices)
            
            voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name=selected_voice
            )
            print(f'Selected voice: {selected_voice}')
            
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
    def get_random_background_video(self, bucket_name="tiktalk-bucket", folder_prefix="background/"):
        """Get a random background video from the specified bucket folder."""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            # List all blobs in the background folder
            blobs = bucket.list_blobs(prefix=folder_prefix)
            
            # Filter for video files
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            video_files = []
            
            for blob in blobs:
                if any(blob.name.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(blob.name)
            
            if not video_files:
                logger.warning(f"No video files found in {bucket_name}/{folder_prefix}")
                # Fallback to the original hardcoded video
                return "https://storage.googleapis.com/tiktalk-bucket/background/Lunatic%20Genji%20Be%20Cuttin!.mp4"
            
            # Select a random video
            random_video = random.choice(video_files)
            video_url = f"https://storage.googleapis.com/{bucket_name}/{random_video}"
            
            logger.info(f"Selected random background video: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"Error getting random background video: {str(e)}")
            # Fallback to the original hardcoded video
            return "https://storage.googleapis.com/tiktalk-bucket/background/Lunatic%20Genji%20Be%20Cuttin!.mp4"

    def get_random_background_music(self, bucket_name="tiktalk-bucket", folder_prefix="music/"):
        """Get a random background music from the specified bucket folder."""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            # List all blobs in the music folder
            blobs = bucket.list_blobs(prefix=folder_prefix)
            
            # Filter for audio files
            audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg']
            music_files = []
            
            for blob in blobs:
                if any(blob.name.lower().endswith(ext) for ext in audio_extensions):
                    music_files.append(blob.name)
            
            if not music_files:
                logger.warning(f"No music files found in {bucket_name}/{folder_prefix}")
                return None
            
            # Select a random music file
            random_music = random.choice(music_files)
            music_url = f"https://storage.googleapis.com/{bucket_name}/{random_music}"
            
            logger.info(f"Selected random background music: {music_url}")
            return music_url
            
        except Exception as e:
            logger.error(f"Error getting random background music: {str(e)}")
            return None

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

    def timeout_handler(self, signum, frame):
        """Handle timeout for video creation"""
        raise TimeoutError("Video creation timed out")

    def create_video_with_timeout(self, background_video_url: str, audio_file: str, output_filename: str, script_text: str = "", timeout_seconds: int = 300):
        """Create video with timeout protection"""
        def target():
            return self.create_video(background_video_url, audio_file, output_filename, script_text)
        
        result = [None]
        exception = [None]
        
        def wrapper():
            try:
                result[0] = target()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            logger.error(f"Video creation timed out after {timeout_seconds} seconds")
            raise TimeoutError(f"Video creation timed out after {timeout_seconds} seconds")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]



    def create_highlighted_text_image(self, text: str, width: int, height: int, current_word_index: int, font_size: int = 28):
        """Create a text image with word-by-word highlighting, showing only 3 lines at a time"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create image with transparent background
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Split text into words
            words = text.split()
            
            # Calculate words per second (assuming 3 words per second for natural reading)
            words_per_second = 3.0
            total_words = len(words)
            
            # Create lines that fit the width (shorter width - 70% instead of 90%)
            max_width = int(width * 0.7)  # Shorter width
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Show only 3 lines at a time, scrolling through them
            lines_per_display = 3
            total_lines = len(lines)
            
            # Calculate which 3 lines to show based on current word index
            if total_lines <= lines_per_display:
                start_line = 0
                end_line = total_lines
            else:
                # Calculate which line the current word is on
                current_line_index = 0
                word_count = 0
                for i, line in enumerate(lines):
                    line_word_count = len(line.split())
                    if word_count + line_word_count > current_word_index:
                        current_line_index = i
                        break
                    word_count += line_word_count
                
                # Show 3 lines centered around current line
                start_line = max(0, current_line_index - 1)
                end_line = min(total_lines, start_line + lines_per_display)
                
                # Adjust if we're near the end
                if end_line - start_line < lines_per_display:
                    start_line = max(0, end_line - lines_per_display)
            
            # Get the lines to display
            display_lines = lines[start_line:end_line]
            
            # Calculate text height for 3 lines
            line_height = font_size + 8
            total_text_height = len(display_lines) * line_height
            
            # Create background rectangle (shorter width)
            bg_width = max_width + 20
            bg_height = total_text_height + 20
            bg_x = (width - bg_width) // 2
            bg_y = height - bg_height - 50
            
            # Draw semi-transparent background
            draw.rectangle([bg_x, bg_y, bg_x + bg_width, bg_y + bg_height], 
                          fill=(0, 0, 0, 200))  # Semi-transparent black
            
            # Draw text lines with highlighting
            text_y = bg_y + 10
            global_word_count = 0
            
            # Calculate the starting word index for the displayed lines
            start_word_index = 0
            for i in range(start_line):
                start_word_index += len(lines[i].split())
            
            
            for line_idx, line in enumerate(display_lines):
                line_words = line.split()
                current_x = bg_x + 10
                
                for word_idx, word in enumerate(line_words):
                    # Calculate the global word index for this word
                    global_word_index = start_word_index + global_word_count
                    is_highlighted = global_word_index == current_word_index
                    
                    # Draw word with white color (no highlighting)
                    word_color = (255, 255, 255, 255)  # White for all words
                    
                    # Get word dimensions
                    bbox = draw.textbbox((0, 0), word, font=font)
                    word_width = bbox[2] - bbox[0]
                    
                    # Draw the word
                    draw.text((current_x, text_y), word, fill=word_color, font=font)
                    
                    # Add space after word (except for last word in line)
                    if word_idx < len(line_words) - 1:
                        space_bbox = draw.textbbox((0, 0), " ", font=font)
                        space_width = space_bbox[2] - space_bbox[0]
                        current_x += word_width + space_width
                    
                    global_word_count += 1
                
                text_y += line_height
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating highlighted text image: {str(e)}")
            return None

    def create_caption_overlay(self, text: str, duration: float, video_width: int, video_height: int):
        """Create a word-by-word highlighted caption overlay with 3 lines at a time."""
        try:
            # Calculate timing for word highlighting based on actual audio duration
            words = text.split()
            total_words = len(words)
            
            # Calculate words per second based on actual audio duration
            words_per_second = total_words / duration if duration > 0 else 3.0
            word_duration = duration / total_words if total_words > 0 else 0.33
            
            # Create a list of ImageClips for each word highlight
            caption_clips = []
            
            for word_index in range(total_words):
                # Calculate time for this word based on actual duration
                start_time = word_index * word_duration
                end_time = min((word_index + 1) * word_duration, duration)
                
                if start_time >= duration:
                    break
                
                # Create highlighted text image for this word
                text_img = self.create_highlighted_text_image(
                    text, video_width, video_height, word_index, font_size=32
                )
                
                if text_img is None:
                    continue
                
                # Save image to temporary file
                with tempfile.NamedTemporaryFile(suffix=f'_{word_index}.png', delete=False) as temp_img:
                    text_img.save(temp_img.name, 'PNG')
                    temp_img_path = temp_img.name
                
                # Create ImageClip for this word
                word_clip = ImageClip(temp_img_path).set_start(start_time).set_duration(end_time - start_time)
                caption_clips.append(word_clip)
                
                # Clean up temporary file
                os.unlink(temp_img_path)
            
            if not caption_clips:
                return None
            
            # Composite all word clips together
            if len(caption_clips) == 1:
                final_clip = caption_clips[0]
            else:
                final_clip = CompositeVideoClip(caption_clips)
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Error creating caption overlay: {str(e)}")
            # Return None if caption creation fails, so video can still be created
            return None

    def create_video(self, background_video_url: str, audio_file: str, output_filename: str, script_text: str = "") -> str:
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
            
            # Get background music
            logger.info("Getting background music...")
            music_url = self.get_random_background_music()
            background_music = None
            
            if music_url:
                try:
                    logger.info(f"Downloading background music from: {music_url}")
                    music_response = requests.get(music_url)
                    if music_response.status_code == 200:
                        # Save music to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_music:
                            temp_music.write(music_response.content)
                            temp_music_path = temp_music.name
                        
                        # Load background music
                        background_music = AudioFileClip(temp_music_path)
                        logger.info("Background music loaded successfully")
                    else:
                        logger.warning(f"Failed to download background music: {music_response.status_code}")
                except Exception as e:
                    logger.error(f"Error loading background music: {str(e)}")
            else:
                logger.info("No background music available")
            
            # If video is longer than audio, trim it to match audio duration
            if video_clip.duration > audio_duration:
                video_clip = video_clip.subclip(0, audio_duration)
            # If video is shorter than audio, loop it to match audio duration
            elif video_clip.duration < audio_duration:
                loops_needed = int(audio_duration / video_clip.duration) + 1
                video_clip = video_clip.loop(loops_needed).subclip(0, audio_duration)
            
            # Resize video to phone dimensions (9:16 aspect ratio)
            # Target resolution: 720x1280 (HD vertical) for good quality/size balance
            target_width = 720
            target_height = 1280
            
            # Resize video to fit phone dimensions while maintaining aspect ratio
            video_clip = video_clip.resize(height=target_height)
            
            # If video is too wide, crop it to 9:16 aspect ratio
            if video_clip.w > target_width:
                # Calculate crop position to center the video
                crop_x = (video_clip.w - target_width) // 2
                video_clip = video_clip.crop(x1=crop_x, x2=crop_x + target_width)
            elif video_clip.w < target_width:
                # If video is too narrow, resize to target width
                video_clip = video_clip.resize(width=target_width)
            
            # Mix script audio with background music
            if background_music:
                try:
                    logger.info("Mixing script audio with background music...")
                    
                    # Adjust background music to match script duration
                    if background_music.duration > audio_duration:
                        background_music = background_music.subclip(0, audio_duration)
                    elif background_music.duration < audio_duration:
                        # Loop background music to match script duration
                        loops_needed = int(audio_duration / background_music.duration) + 1
                        background_music = background_music.loop(loops_needed).subclip(0, audio_duration)
                    
                    # Lower the volume of background music (30% of original)
                    background_music = background_music.volumex(0.3)
                    
                    # Increase script audio volume slightly (110% of original) for better clarity
                    audio_clip = audio_clip.volumex(1.1)
                    
                    # Mix the two audio tracks
                    mixed_audio = CompositeAudioClip([audio_clip, background_music])
                    logger.info("Audio mixing completed successfully")
                    
                except Exception as e:
                    logger.error(f"Error mixing audio: {str(e)}, using script audio only")
                    mixed_audio = audio_clip
            else:
                logger.info("No background music, using script audio only")
                mixed_audio = audio_clip
            
            # Set the audio of the video clip to the mixed audio
            video_with_audio = video_clip.set_audio(mixed_audio)
            
            # Add caption overlay if script text is provided
            if script_text.strip():
                try:
                    # Create caption overlay
                    caption_overlay = self.create_caption_overlay(
                        script_text, 
                        audio_duration, 
                        target_width, 
                        target_height
                    )
                    
                    # Composite overlays
                    if caption_overlay is not None:
                        final_video = CompositeVideoClip([video_with_audio, caption_overlay])
                    else:
                        final_video = video_with_audio
                        
                except Exception as e:
                    logger.error(f"Error adding caption overlay: {str(e)}, creating video without overlays")
                    final_video = video_with_audio
            else:
                final_video = video_with_audio
            
            # Write the result to file with simplified settings
            logger.info(f"Writing video to file: {output_filename}")
            try:
                # Use simpler settings to avoid getting stuck
                final_video.write_videofile(
                    output_filename,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None,
                    # Balanced quality and speed settings
                    fps=24,  # Standard FPS for good quality
                    preset='fast',  # Good balance of speed and quality
                    ffmpeg_params=['-crf', '23', '-movflags', '+faststart', '-threads', '4']  # Better quality, reasonable speed
                )
                logger.info(f"Video file written successfully: {output_filename}")
            except Exception as e:
                logger.error(f"Error writing video file: {str(e)}")
                # Try with even simpler settings
                logger.info("Retrying with minimal settings...")
                final_video.write_videofile(
                    output_filename,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None,
                    preset='fast',
                    fps=24,
                    ffmpeg_params=['-crf', '25', '-threads', '4']
                )
                logger.info(f"Video file written with fallback settings: {output_filename}")
            
            # Clean up
            video_clip.close()
            audio_clip.close()
            if background_music:
                background_music.close()
            final_video.close()
            os.unlink(temp_video_path)
            
            # Clean up temporary music file if it exists
            if 'temp_music_path' in locals() and os.path.exists(temp_music_path):
                os.unlink(temp_music_path)
            
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

            # Use the entire script as one video (since it's designed to be one continuous piece)
            paragraphs = [script.strip()] if script.strip() else []

            # Select a random voice for this entire message (consistent across all audio)
            voices = [
                "en-US-Wavenet-A",  # Male, American
                "en-US-Wavenet-B",  # Male, American
                "en-US-Wavenet-C",  # Female, American
                "en-US-Wavenet-D",  # Male, American
                "en-US-Wavenet-E",  # Female, American
                "en-US-Wavenet-F",  # Female, American
                "en-US-Standard-A", # Male, American
                "en-US-Standard-B", # Male, American
                "en-US-Standard-C", # Female, American
                "en-US-Standard-D", # Male, American
                "en-US-Standard-E", # Female, American
                "en-US-Standard-F", # Female, American
            ]
            selected_voice = random.choice(voices)
            logger.info(f"Selected voice for this message: {selected_voice}")

            # Loop through paragraphs and generate audio with consistent voice
            for i, para in enumerate(paragraphs, start=1):
                output_filename = f"output_{i}.mp3"
                self.audio(para, output_filename=output_filename, voice_name=selected_voice)
                print(f"Audio generated: {output_filename}")


            # Create videos by combining background video with each audio file
            video_links = []
            
            for i in range(1, len(paragraphs) + 1):
                audio_file = f"output_{i}.mp3"
                video_file = f"video_{i}.mp4"
                
                if os.path.exists(audio_file):
                    try:
                        logger.info(f"Creating video {i} with audio file: {audio_file}")
                        
                        # Get a random background video for each video
                        background_video_url = self.get_random_background_video()
                        logger.info(f"Using background video: {background_video_url}")
                        
                        # Pass the corresponding paragraph as script text for captions
                        script_text = paragraphs[i-1] if i <= len(paragraphs) else ""
                        
                        # Create the video with timeout protection
                        self.create_video_with_timeout(background_video_url, audio_file, video_file, script_text, timeout_seconds=120)
                        
                        # Check if video file was created successfully
                        if os.path.exists(video_file):
                            logger.info(f"Video created successfully: {video_file}")
                            print(f"Video created: {video_file}")
                        else:
                            logger.error(f"Video file was not created: {video_file}")
                            raise Exception(f"Video file creation failed: {video_file}")
                        
                        # Upload video to Google Cloud Storage
                        video_path = f"videos/{notes_id}/video_{i}.mp4"
                        logger.info(f"Uploading video to: {video_path}")
                        self.upload_blob("tiktalk-bucket", video_file, video_path)
                        logger.info(f"Video uploaded successfully: {video_path}")
                        print(f"Video uploaded: {video_path}")
                        
                        # Add video link to the list
                        video_url = f"https://storage.googleapis.com/tiktalk-bucket/{video_path}"
                        video_links.append(video_url)
                        logger.info(f"Added video URL to list: {video_url}")
                        
                        # Delete local audio file after successful video creation and upload
                        os.remove(audio_file)
                        logger.info(f"Deleted local audio file: {audio_file}")
                        
                    except Exception as e:
                        logger.error(f"Error creating video {i}: {str(e)}")
                        print(f"Error creating video {i}: {str(e)}")
                        # Clean up audio file even if video creation failed
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
                            logger.info(f"Cleaned up audio file after error: {audio_file}")
                else:
                    logger.warning(f"Audio file not found: {audio_file}")
                    print(f"Audio file not found: {audio_file}")

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

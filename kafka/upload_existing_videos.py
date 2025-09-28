#!/usr/bin/env python3
"""
Script to upload existing videos to Google Cloud Storage with user_id/post_id structure
"""

import os
import sys
import logging
from google.cloud import storage

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # delete existing object if it exists
    if blob.exists(): 
        blob.delete()
        logger.info(f"Deleted existing blob: {destination_blob_name}")

    generation_match_precondition=0

    # upload to storage bucket
    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    logger.info(f"File {source_file_name} uploaded to {destination_blob_name}.")

def upload_existing_videos():
    """Upload existing videos to Google Cloud Storage with user_id/post_id structure"""
    
    # Configuration - you can modify these values
    user_id = "test-user"  # Change this to the actual user ID
    post_id = "test-post"  # Change this to the actual post ID
    
    bucket_name = "tiktalk-bucket"
    
    # Find all video files in the current directory
    video_files = []
    for i in range(1, 10):  # Check for video_1.mp4 to video_9.mp4
        video_file = f"video_{i}.mp4"
        if os.path.exists(video_file):
            video_files.append(video_file)
            logger.info(f"Found video file: {video_file}")
    
    if not video_files:
        logger.error("No video files found in the current directory")
        return
    
    logger.info(f"Found {len(video_files)} video files to upload")
    logger.info(f"Uploading to: {bucket_name}/{user_id}/{post_id}/")
    
    # Upload each video file
    for i, video_file in enumerate(video_files, start=1):
        destination_path = f"{user_id}/{post_id}/video_{i}.mp4"
        
        try:
            logger.info(f"Uploading {video_file} to {destination_path}")
            upload_blob(bucket_name, video_file, destination_path)
            logger.info(f"Successfully uploaded: {destination_path}")
            
        except Exception as e:
            logger.error(f"Error uploading {video_file}: {str(e)}")

if __name__ == "__main__":
    upload_existing_videos()

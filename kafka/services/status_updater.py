"""
Status Updater Service for TikTalk Kafka Consumer
Periodically updates notes status and video links via API calls
"""

import requests
import time
import logging
import random
import string
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StatusUpdater:
    def __init__(self, api_base_url: str = "http://localhost:5001"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
    def generate_fake_video_links(self, count: int = 3) -> str:
        """Generate fake video links for testing"""
        video_links = []
        for i in range(count):
            # Generate random string for fake video ID
            video_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            video_link = f"https://storage.googleapis.com/tiktalk-bucket/videos/{video_id}.mp4"
            video_links.append(video_link)
        return ",".join(video_links)
    
    def update_notes_status(self, notes_id: int, status: str, videos_link: str = None) -> bool:
        """Update notes status via internal API call (no authentication required)"""
        try:
            # Use internal API endpoint that doesn't require authentication
            url = f"{self.api_base_url}/api/internal/notes/{notes_id}/status"
            
            payload = {
                "status": status
            }
            
            if videos_link:
                payload["videos_link"] = videos_link
            
            # No authentication headers needed for internal API
            headers = {
                "Content-Type": "application/json"
            }
            
            response = self.session.patch(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully updated notes {notes_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update notes {notes_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating notes {notes_id}: {str(e)}")
            return False
    
    def mark_as_started(self, notes_id: int) -> bool:
        """Mark notes as started when processing begins"""
        try:
            logger.info(f"Marking notes {notes_id} as 'started'")
            return self.update_notes_status(notes_id, "started")
        except Exception as e:
            logger.error(f"Error marking notes {notes_id} as started: {str(e)}")
            return False
    
    def mark_as_completed(self, notes_id: int) -> bool:
        """Mark notes as completed when processing is done"""
        try:
            fake_video_links = self.generate_fake_video_links(3)
            logger.info(f"Marking notes {notes_id} as 'completed' with video links: {fake_video_links}")
            return self.update_notes_status(notes_id, "completed", fake_video_links)
        except Exception as e:
            logger.error(f"Error marking notes {notes_id} as completed: {str(e)}")
            return False

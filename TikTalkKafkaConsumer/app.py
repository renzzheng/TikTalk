#!/usr/bin/env python3
"""
App entry point for TikTalk Kafka Consumer
"""

import sys
import logging
from services.pdf_consumer import TikTalkKafkaConsumer

logger = logging.getLogger(__name__)

def main():
    try:
        consumer = TikTalkKafkaConsumer()
        consumer.run()
    except Exception as e:
        logger.error(f"Failed to start consumer: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

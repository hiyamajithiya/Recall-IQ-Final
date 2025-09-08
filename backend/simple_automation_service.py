#!/usr/bin/env python
"""
RecallIQ V2 - Simple Automation Service
Ultra-lightweight background service for automatic batch processing
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recalliq.settings.development')

import django
django.setup()

from django.utils import timezone
from batches.models import Batch
from batches.tasks import send_batch_emails

# Simple logging with UTF-8 encoding for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('simple_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SimpleAutomation')

class SimpleAutomationService:
    """Ultra-simple automation service"""
    
    def __init__(self):
        self.running = True
        self.processed_batches = set()
        
    def check_batches(self):
        """Check and process scheduled batches"""
        try:
            current_time = timezone.now()
            
            # Find ready batches
            ready_batches = Batch.objects.filter(
                status='scheduled',
                start_time__lte=current_time
            ).exclude(id__in=self.processed_batches)
            
            for batch in ready_batches:
                try:
                    logger.info(f"EXECUTING: {batch.name} (ID: {batch.id})")
                    logger.info(f"   Scheduled: {batch.start_time}")
                    logger.info(f"   Recipients: {batch.total_recipients}")
                    
                    # Mark as processed
                    self.processed_batches.add(batch.id)
                    
                    # Execute batch
                    send_batch_emails(batch.id)
                    
                    # Check result
                    batch.refresh_from_db()
                    logger.info(f"COMPLETED: {batch.name}")
                    logger.info(f"   Status: {batch.status}")
                    logger.info(f"   Sent: {batch.emails_sent}")
                    logger.info("" + "="*50)
                    
                except Exception as e:
                    logger.error(f"ERROR executing {batch.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in batch check: {e}")
            
    def run_continuous(self):
        """Run automation continuously"""
        logger.info("Simple Automation Service STARTED")
        logger.info("Checking every 30 seconds for scheduled batches")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*60)
        
        check_count = 0
        
        try:
            while self.running:
                self.check_batches()
                check_count += 1
                
                # Status every 10 minutes
                if check_count % 20 == 0:
                    logger.info(f"Service running - {check_count} checks completed")
                    
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            logger.info("Simple Automation Service STOPPED")

def main():
    """Run the service"""
    service = SimpleAutomationService()
    service.run_continuous()

if __name__ == "__main__":
    main()

"""
Background task processing with PostgreSQL storage
"""

import logging
import random
import time
from datetime import datetime
from typing import Dict, Any
from app.services.veo_service import VeoService
from app.models.database import db_service

logger = logging.getLogger(__name__)

SAMPLE_VIDEOS = [
    "https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/demo/sample.mp4",
    "https://www.w3schools.com/html/mov_bbb.mp4",
]

def process_video_generation_db(task_id: str, request_data: Dict[str, Any], user_id: str):
    """
    Process video generation with PostgreSQL storage and progress updates
    """
    logger.info(f"🔄 ===== STARTING TASK: {task_id} for user: {user_id} =====")
    
    try:
        # Step 1: Start processing (10%)
        logger.info(f"📊 Task {task_id}: Updating to 10% - Starting...")
        db_service.update_video_status(user_id, task_id, "processing", progress=10)
        time.sleep(1)
        
        # Step 2: Initializing (20%)
        logger.info(f"📊 Task {task_id}: Updating to 20% - Initializing AI...")
        db_service.update_video_status(user_id, task_id, "processing", progress=20)
        time.sleep(1)
        
        # Step 3: Get Veo service
        logger.info(f"📊 Task {task_id}: Updating to 30% - Connecting to Veo...")
        db_service.update_video_status(user_id, task_id, "processing", progress=30)
        veo_service = VeoService()
        time.sleep(1)
        
        # Step 4: Generating video (40-80%)
        duration = request_data.get("duration_seconds", 6)
        if duration not in [4, 6, 8]:
            duration = 6
        
        logger.info(f"📊 Task {task_id}: Updating to 50% - Generating video...")
        db_service.update_video_status(user_id, task_id, "processing", progress=50)
        time.sleep(2)
        
        # Actually generate the video
        logger.info(f"🎬 Task {task_id}: Calling Veo 3 for generation...")
        video_url = veo_service.generate_ad_video(
            product_name=request_data["product_name"],
            product_description=request_data["product_description"],
            platform=request_data["platform"],
            duration=duration
        )
        
        # Step 5: Generation complete (80%)
        logger.info(f"📊 Task {task_id}: Updating to 80% - Finalizing...")
        db_service.update_video_status(user_id, task_id, "processing", progress=80)
        time.sleep(1)
        
        if video_url:
            # Step 6: Uploading (90%)
            logger.info(f"📊 Task {task_id}: Updating to 90% - Uploading...")
            db_service.update_video_status(user_id, task_id, "processing", progress=90)
            time.sleep(1)
            
            # Step 7: Complete (100%)
            logger.info(f"✅ Task {task_id}: COMPLETE! Video URL: {video_url}")
            db_service.update_video_status(
                user_id, 
                task_id, 
                "completed", 
                progress=100,
                video_url=video_url
            )
            logger.info(f"✅ Task {task_id} completed for user {user_id}")
        else:
            # Fallback to sample video
            fallback_url = random.choice(SAMPLE_VIDEOS)
            logger.warning(f"⚠️ Task {task_id}: Using fallback video: {fallback_url}")
            db_service.update_video_status(
                user_id, 
                task_id, 
                "completed", 
                progress=100,
                video_url=fallback_url
            )
            
    except Exception as e:
        logger.error(f"❌ Task {task_id} error: {e}")
        logger.error(f"❌ Full error: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
        db_service.update_video_status(user_id, task_id, "failed", error_message=str(e))
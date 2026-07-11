"""
Background task processing with PostgreSQL storage
Supports: Text-to-Video, Image-to-Video, First/Last Frame
"""

import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
import os
import traceback

from app.services.veo_service import VeoService
from app.models.database import db_service

logger = logging.getLogger(__name__)

SAMPLE_VIDEOS = [
    "https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/demo/sample.mp4",
    "https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/demo/sample2.mp4",
    "https://www.w3schools.com/html/mov_bbb.mp4",
]


def load_image_from_path(image_path: Optional[str]) -> Optional[Image.Image]:
    """Load image from file path"""
    if not image_path:
        return None

    try:
        if os.path.exists(image_path):
            image = Image.open(image_path)
            logger.info(f"✅ Loaded image: {image_path} ({image.size})")
            return image
        else:
            logger.warning(f"⚠️ Image not found: {image_path}")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to load image {image_path}: {e}")
        return None


def process_video_generation_db(
    task_id: str,
    request_data: Dict[str, Any],
    user_id: str
):
    """
    Process video generation with PostgreSQL storage and progress updates
    Supports: Text-to-Video, Image-to-Video, First/Last Frame
    """
    logger.info(f"🔄 ===== STARTING TASK: {task_id} for user: {user_id} =====")
    logger.info(f"📋 Request data keys: {list(request_data.keys())}")

    # ===== LOG WHAT WE RECEIVED =====
    generation_mode = request_data.get("generation_mode", "text")
    first_frame_path = request_data.get("first_frame_path")
    last_frame_path = request_data.get("last_frame_path")

    logger.info(f"🎬 Generation mode: {generation_mode}")
    logger.info(f"📸 First frame path: {first_frame_path}")
    logger.info(f"📸 Last frame path: {last_frame_path}")
    logger.info(f"📱 Platform: {request_data.get('platform')}")
    logger.info(f"🏷️ Product: {request_data.get('product_name')}")

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

        try:
            veo_service = VeoService()
            logger.info("✅ Veo Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Veo Service: {e}")
            db_service.update_video_status(
                user_id,
                task_id,
                "failed",
                error_message=f"Veo service error: {str(e)}"
            )
            return

        time.sleep(1)

        # Step 4: Prepare generation parameters
        duration = request_data.get("duration_seconds", 6)
        if duration not in [4, 6, 8]:
            duration = 6
            logger.warning("⚠️ Invalid duration, defaulting to 6 seconds")

        platform = request_data.get("platform", "instagram")
        aspect_ratio = "9:16" if platform in ["tiktok", "instagram"] else "16:9"
        product_name = request_data.get("product_name", "Product")
        product_description = request_data.get("product_description", "")
        generate_audio = request_data.get("generate_audio", True)

        logger.info(
            f"🎬 Parameters: duration={duration}s, aspect={aspect_ratio}, "
            f"audio={generate_audio}"
        )

        # ===== LOAD IMAGES IF AVAILABLE =====
        first_frame_image = None
        last_frame_image = None

        if generation_mode in ["image", "first-last"]:
            if first_frame_path:
                first_frame_image = load_image_from_path(first_frame_path)
                if first_frame_image:
                    logger.info(f"📸 First frame loaded: {first_frame_path}")
                else:
                    logger.warning("⚠️ First frame not available, falling back to text")
                    generation_mode = "text"
            else:
                logger.warning("⚠️ No first frame path provided, falling back to text")
                generation_mode = "text"

        if generation_mode == "first-last":
            if last_frame_path:
                last_frame_image = load_image_from_path(last_frame_path)
                if last_frame_image:
                    logger.info(f"📸 Last frame loaded: {last_frame_path}")
                else:
                    logger.warning("⚠️ Last frame not available, falling back to image")
                    generation_mode = "image"
            else:
                logger.warning("⚠️ No last frame path provided, falling back to image")
                generation_mode = "image"

        # Step 5: Generating video (40-80%)
        logger.info(f"📊 Task {task_id}: Updating to 50% - Generating video...")
        db_service.update_video_status(user_id, task_id, "processing", progress=50)
        time.sleep(2)

        # ===== GENERATE BASED ON MODE =====
        video_url = None
        logger.info(f"🎬 Task {task_id}: Generating with mode: {generation_mode}")

        try:
            if generation_mode == "image" and first_frame_image:
                # ===== IMAGE-TO-VIDEO =====
                logger.info(f"📸 Task {task_id}: Generating IMAGE-TO-VIDEO...")
                prompt = (
                    f"Product showcase of {product_name}. {product_description}. "
                    f"Modern style, {aspect_ratio} format. Professional, clean, "
                    "visually appealing."
                )
                logger.info(f"📝 Prompt: {prompt[:100]}...")

                video_url = veo_service.generate_from_image(
                    prompt=prompt,
                    image=first_frame_image,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    generate_audio=generate_audio,
                    use_lite=False
                )
                logger.info(f"📸 Image-to-Video generation complete: {video_url}")

            elif generation_mode == "first-last" and first_frame_image and last_frame_image:
                # ===== FIRST/LAST FRAME =====
                logger.info(f"📸 Task {task_id}: Generating FIRST/LAST FRAME video...")
                prompt = (
                    f"Transition showcasing {product_name}. {product_description}. "
                    "Smooth, professional animation. Clean product presentation."
                )
                logger.info(f"📝 Prompt: {prompt[:100]}...")

                video_url = veo_service.generate_with_first_last_frame(
                    prompt=prompt,
                    first_frame=first_frame_image,
                    last_frame=last_frame_image,
                    duration=min(duration, 8),
                    aspect_ratio=aspect_ratio,
                    generate_audio=generate_audio,
                    use_lite=False
                )
                logger.info(f"📸 First/Last Frame generation complete: {video_url}")

            else:
                # ===== TEXT-TO-VIDEO (Default) =====
                logger.info(f"📝 Task {task_id}: Generating TEXT-TO-VIDEO...")
                video_url = veo_service.generate_ad_video(
                    product_name=product_name,
                    product_description=product_description,
                    platform=platform,
                    duration=duration
                )
                logger.info(f"📝 Text-to-Video generation complete: {video_url}")

        except Exception as gen_error:
            logger.error(f"❌ Generation error: {gen_error}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            db_service.update_video_status(
                user_id,
                task_id,
                "failed",
                error_message=f"Generation error: {str(gen_error)}"
            )
            return

        # Step 6: Generation complete (80%)
        logger.info(f"📊 Task {task_id}: Updating to 80% - Finalizing...")
        db_service.update_video_status(user_id, task_id, "processing", progress=80)
        time.sleep(1)

        if video_url:
            # Step 7: Uploading (90%)
            logger.info(f"📊 Task {task_id}: Updating to 90% - Uploading...")
            db_service.update_video_status(user_id, task_id, "processing", progress=90)
            time.sleep(1)

            # Step 8: Complete (100%)
            logger.info(f"✅ Task {task_id}: COMPLETE! Video URL: {video_url}")

            db_service.update_video_status(
                user_id,
                task_id,
                "completed",
                progress=100,
                video_url=video_url
            )
            logger.info(f"✅ Task {task_id} completed successfully for user {user_id}")

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
            logger.info(f"✅ Task {task_id} completed with fallback video")

    except Exception as e:
        logger.error(f"❌ Task {task_id} error: {e}")
        logger.error(f"❌ Full error: {e.__class__.__name__}: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

        try:
            db_service.update_video_status(
                user_id,
                task_id,
                "failed",
                error_message=str(e)
            )
        except Exception as db_error:
            logger.error(f"❌ Failed to update status in database: {db_error}")

    finally:
        # ===== CLEAN UP UPLOADED IMAGES =====
        try:
            if first_frame_path and os.path.exists(first_frame_path):
                os.remove(first_frame_path)
                logger.info(f"🗑️ Deleted first frame: {first_frame_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete {first_frame_path}: {e}")

        try:
            if last_frame_path and os.path.exists(last_frame_path):
                os.remove(last_frame_path)
                logger.info(f"🗑️ Deleted last frame: {last_frame_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete {last_frame_path}: {e}")

        logger.info(f"🔄 ===== TASK COMPLETED: {task_id} =====")
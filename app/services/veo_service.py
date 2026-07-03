"""
Real AI Video Generation using Google's Gen AI SDK for Veo 3
Using GA model with proven response extraction
"""

import time
import logging
import uuid
from typing import Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class VeoService:
    def __init__(self):
        """Initialize the Veo 3 service using Google Gen AI SDK"""
        self.project_id = "ai-social-ad-generator"
        self.location = "us-central1"
        self.bucket_name = "ai-ad-videos-kamlesh-2026"
        
        try:
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            logger.info("✅ Gen AI SDK initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gen AI SDK: {e}")
            raise

    def generate_video(
        self, 
        prompt: str, 
        duration: int = 6, 
        aspect_ratio: str = "16:9",
        resolution: str = "1080p",
        enhance_prompt: bool = True,
        generate_audio: bool = True
    ) -> Optional[str]:
        """
        Generate a video using Veo 3.1 GA model
        
        Args:
            prompt: Text description of the video
            duration: Length in seconds (4, 6, or 8)
            aspect_ratio: "16:9", "9:16", or "1:1"
            resolution: "1080p", "720p", or "4k"
            enhance_prompt: Whether to enhance the prompt
            generate_audio: Whether to generate audio
        
        Returns:
            Public URL of the generated video, or None if failed
        """
        try:
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            logger.info(f"⏳ Generating video... (this will take 2-3 minutes)")
            
            # Use the GA model (confirmed working)
            video_model = "veo-3.1-generate-001"
            
            # Create timestamped output path
            timestamp = int(time.time())
            output_gcs_uri = f"gs://{self.bucket_name}/generated/veo_{timestamp}/"
            
            logger.info(f"📁 Output path: {output_gcs_uri}")
            logger.info(f"🚀 Starting Veo 3 generation...")
            
            # Start the generation operation
            operation = self.client.models.generate_videos(
                model=video_model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                    duration_seconds=duration,
                    resolution=resolution,
                    person_generation="allow_adult",
                    enhance_prompt=enhance_prompt,
                    generate_audio=generate_audio,
                    output_gcs_uri=output_gcs_uri,
                ),
            )
            
            logger.info(f"📋 Operation started: {operation.name}")
            
            # Wait for completion with progress updates
            timeout = 300  # 5 minutes
            start_time = time.time()
            last_log_time = start_time
            
            while not operation.done:
                elapsed = int(time.time() - start_time)
                
                if time.time() - last_log_time > 15:
                    logger.info(f"⏳ Still generating... ({elapsed}s elapsed)")
                    last_log_time = time.time()
                
                if elapsed > timeout:
                    logger.error(f"❌ Video generation timed out after {timeout}s")
                    return None
                
                time.sleep(15)  # Poll every 15 seconds
                operation = self.client.operations.get(operation)
            
            logger.info(f"✅ Operation completed after {int(time.time() - start_time)}s")
            
            # Check for errors
            if operation.error:
                logger.error(f"❌ Operation error: {operation.error}")
                return None
            
            # 🔥 CORRECT: Extract video from operation.result
            if operation.result and operation.result.generated_videos:
                video_obj = operation.result.generated_videos[0]
                
                # The video URI is in video.uri
                if hasattr(video_obj, 'video') and hasattr(video_obj.video, 'uri'):
                    video_uri = video_obj.video.uri
                    logger.info(f"✅ Video generated successfully!")
                    logger.info(f"📹 Video URI: {video_uri}")
                    
                    # Convert to public URL
                    if video_uri.startswith("gs://"):
                        public_url = video_uri.replace("gs://", "https://storage.googleapis.com/")
                        logger.info(f"🔗 Public URL: {public_url}")
                        return public_url
                    return video_uri
                else:
                    logger.error("❌ No video URI found in result")
                    return None
            else:
                logger.error("❌ No generated_videos in result")
                return None
                
        except Exception as e:
            logger.error(f"❌ AI Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_ad_video(
        self,
        product_name: str,
        product_description: str,
        platform: str,
        duration: int = 6
    ) -> Optional[str]:
        """
        Generate a social media ad video
        
        Args:
            product_name: Name of the product
            product_description: Description of the product
            platform: Target platform (tiktok, instagram, youtube)
            duration: Video length in seconds (4, 6, or 8)
        
        Returns:
            Public URL of the generated video
        """
        # Craft platform-specific prompts
        prompts = {
            "tiktok": f"Product showcase of {product_name}. {product_description}. Modern style, fast-paced, 9:16 format, vibrant colors, TikTok style.",
            "instagram": f"Product showcase of {product_name}. {product_description}. Clean style, aesthetic, 9:16 format, Instagram Reel style.",
            "youtube": f"Product showcase of {product_name}. {product_description}. Professional style, cinematic, 16:9 format, YouTube ad style."
        }
        
        prompt = prompts.get(platform, prompts["instagram"])
        aspect_ratio = "9:16" if platform in ["tiktok", "instagram"] else "16:9"
        
        # Ensure duration is valid (4, 6, or 8 seconds)
        if duration not in [4, 6, 8]:
            duration = 6
        
        return self.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution="1080p",
            enhance_prompt=True,
            generate_audio=True
        )
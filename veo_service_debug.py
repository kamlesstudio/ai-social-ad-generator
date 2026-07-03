# """
# Real AI Video Generation using Google's Gen AI SDK for Veo 3
# Fixed: Using preview model and correct response parsing
# """

# import os
# import time
# import logging
# import base64
# import uuid
# from typing import Optional
# from google import genai
# from google.genai import types

# logger = logging.getLogger(__name__)

# class VeoService:
#     def __init__(self):
#         """Initialize the Veo 3 service using Google Gen AI SDK"""
#         self.project_id = "ai-social-ad-generator"
#         self.location = "us-central1"
#         self.bucket_name = "ai-ad-videos-kamlesh-2026"
        
#         try:
#             self.client = genai.Client(
#                 vertexai=True,
#                 project=self.project_id,
#                 location=self.location
#             )
#             logger.info("✅ Gen AI SDK initialized successfully")
#         except Exception as e:
#             logger.error(f"❌ Failed to initialize Gen AI SDK: {e}")
#             raise

#     def generate_video(
#         self, 
#         prompt: str, 
#         duration: int = 6, 
#         aspect_ratio: str = "16:9",
#         resolution: str = "1080p",
#         enhance_prompt: bool = True,
#         generate_audio: bool = True
#     ) -> Optional[str]:
#         """
#         Generate a video using Veo 3 via Google Gen AI SDK
#         """
#         try:
#             logger.info(f"📝 Prompt: {prompt[:100]}...")
#             logger.info(f"⏳ Generating video... (this will take 1-3 minutes)")
            
#             # 🔥 FIX: Use preview model for v1beta1 endpoint compatibility
#             # veo-3.1-generate-preview works with beta endpoint
#             video_model = "veo-3.1-generate-preview"
#             logger.info(f"📋 Using model: {video_model}")
            
#             # Generate timestamp for output path
#             timestamp = int(time.time())
#             output_path = f"gs://{self.bucket_name}/generated/veo_{timestamp}/"
#             logger.info(f"📁 Output will be saved to: {output_path}")
            
#             # Start the generation operation
#             operation = self.client.models.generate_videos(
#                 model=video_model,
#                 prompt=prompt,
#                 config=types.GenerateVideosConfig(
#                     aspect_ratio=aspect_ratio,
#                     number_of_videos=1,
#                     duration_seconds=duration,
#                     resolution=resolution,
#                     person_generation="allow_adult",
#                     enhance_prompt=enhance_prompt,
#                     generate_audio=generate_audio,
#                     output_gcs_uri=output_path,
#                 ),
#             )
            
#             logger.info(f"📋 Operation started: {operation.name}")
            
#             # Wait for completion with progress updates
#             timeout = 300  # 5 minutes
#             start_time = time.time()
#             last_log_time = start_time
            
#             while not operation.done:
#                 elapsed = int(time.time() - start_time)
                
#                 if time.time() - last_log_time > 15:
#                     logger.info(f"⏳ Still generating... ({elapsed}s elapsed)")
#                     last_log_time = time.time()
                
#                 if elapsed > timeout:
#                     logger.error(f"❌ Video generation timed out after {timeout}s")
#                     return None
                
#                 # 🔥 FIX: Wait 15 seconds between polls (avoid rate limits)
#                 time.sleep(15)
#                 operation = self.client.operations.get(operation)
            
#             logger.info(f"✅ Operation completed after {int(time.time() - start_time)}s")
            
#             # Check for errors
#             if operation.error:
#                 logger.error(f"❌ Operation error: {operation.error}")
#                 return None
            
#             # Extract video URL
#             video_url = self._extract_video_from_result(operation.result)
            
#             if video_url:
#                 logger.info(f"✅ Video generated successfully!")
#                 logger.info(f"📹 URL: {video_url}")
#                 return video_url
#             else:
#                 # 🔥 FALLBACK: Check if video was written to GCS but SDK couldn't parse
#                 logger.warning("⚠️ SDK returned no video URL, checking GCS bucket...")
#                 gcs_video = self._check_gcs_for_video(timestamp)
#                 if gcs_video:
#                     return gcs_video
                
#                 logger.error("❌ No video URL found in result")
#                 return None
                
#         except Exception as e:
#             logger.error(f"❌ AI Generation Error: {e}")
#             import traceback
#             traceback.print_exc()
#             return None

#     def _extract_video_from_result(self, result) -> Optional[str]:
#         """
#         🔥 FIX: Correct extraction for Veo 3.1 preview model
#         Response structure: result.generated_videos[0].video.uri
#         """
#         if not result:
#             logger.warning("⚠️ Result is None")
#             return None
        
#         logger.info(f"🔍 Extracting video from result: {type(result)}")
        
#         try:
#             # Check for generated_videos list
#             if hasattr(result, 'generated_videos') and result.generated_videos:
#                 logger.info(f"📹 Found {len(result.generated_videos)} generated videos")
                
#                 # Get the first video
#                 video_obj = result.generated_videos[0]
#                 logger.info(f"📹 Video object: {video_obj}")
                
#                 # The video object has a 'video' attribute with 'uri'
#                 if hasattr(video_obj, 'video'):
#                     video_data = video_obj.video
#                     logger.info(f"📹 Video data: {video_data}")
                    
#                     # Check for URI
#                     if hasattr(video_data, 'uri'):
#                         uri = video_data.uri
#                         logger.info(f"📹 URI: {uri}")
#                         if uri:
#                             if uri.startswith("gs://"):
#                                 return uri.replace("gs://", "https://storage.googleapis.com/")
#                             return uri
                    
#                     # Check for video_bytes
#                     if hasattr(video_data, 'video_bytes'):
#                         video_bytes = video_data.video_bytes
#                         logger.info(f"📹 Video bytes size: {len(video_bytes)}")
#                         if video_bytes:
#                             return self._save_to_bucket_with_retry(video_bytes)
                
#                 # Check for gcs_uri directly
#                 if hasattr(video_obj, 'gcs_uri'):
#                     gcs_uri = video_obj.gcs_uri
#                     logger.info(f"📹 GCS URI: {gcs_uri}")
#                     if gcs_uri:
#                         if gcs_uri.startswith("gs://"):
#                             return gcs_uri.replace("gs://", "https://storage.googleapis.com/")
#                         return gcs_uri
                
#                 # Check for uri directly
#                 if hasattr(video_obj, 'uri'):
#                     uri = video_obj.uri
#                     logger.info(f"📹 URI (direct): {uri}")
#                     if uri:
#                         if uri.startswith("gs://"):
#                             return uri.replace("gs://", "https://storage.googleapis.com/")
#                         return uri
            
#             # Fallback: check for video_uri
#             if hasattr(result, 'video_uri'):
#                 video_uri = result.video_uri
#                 logger.info(f"📹 Video URI (fallback): {video_uri}")
#                 if video_uri:
#                     if video_uri.startswith("gs://"):
#                         return video_uri.replace("gs://", "https://storage.googleapis.com/")
#                     return video_uri
            
#             logger.warning("⚠️ No video found in response")
#             return None
            
#         except Exception as e:
#             logger.error(f"❌ Extraction failed: {e}")
#             import traceback
#             traceback.print_exc()
#             return None

#     def _check_gcs_for_video(self, timestamp: int) -> Optional[str]:
#         """
#         🔥 FALLBACK: Check if video was written to GCS bucket
#         """
#         try:
#             from google.cloud import storage
            
#             storage_client = storage.Client(project=self.project_id)
#             bucket = storage_client.bucket(self.bucket_name)
            
#             # Check the generated folder for this timestamp
#             prefix = f"generated/veo_{timestamp}/"
#             logger.info(f"🔍 Checking GCS for: {prefix}")
            
#             blobs = list(bucket.list_blobs(prefix=prefix))
            
#             if blobs:
#                 logger.info(f"📦 Found {len(blobs)} files in GCS")
#                 for blob in blobs:
#                     logger.info(f"📹 Found file: {blob.name}")
#                     # Make it public if not already
#                     if not blob.public_url:
#                         blob.make_public()
#                     return blob.public_url
#             else:
#                 logger.warning(f"⚠️ No files found in {prefix}")
            
#             return None
            
#         except Exception as e:
#             logger.error(f"❌ GCS check failed: {e}")
#             return None

#     def _save_to_bucket_with_retry(self, video_data: bytes, max_retries: int = 3) -> Optional[str]:
#         """Save video to bucket with retry logic"""
#         if not video_data or len(video_data) < 1000:
#             logger.warning(f"⚠️ Video data too small: {len(video_data)} bytes")
#             return None
            
#         for attempt in range(max_retries):
#             try:
#                 logger.info(f"🔄 Upload attempt {attempt + 1}/{max_retries} ({len(video_data)} bytes)")
#                 result = self._save_to_bucket(video_data)
#                 if result:
#                     return result
#                 time.sleep(5)
#             except Exception as e:
#                 logger.warning(f"⚠️ Upload attempt {attempt + 1} failed: {e}")
#                 time.sleep(5)
        
#         logger.error("❌ All upload attempts failed")
#         return None

#     def _save_to_bucket(self, video_data: bytes) -> Optional[str]:
#         """Save video bytes to your GCP bucket"""
#         try:
#             from google.cloud import storage
            
#             storage_client = storage.Client(project=self.project_id)
#             bucket = storage_client.bucket(self.bucket_name)
            
#             timestamp = int(time.time())
#             filename = f"generated/veo_{timestamp}_{uuid.uuid4().hex[:6]}.mp4"
            
#             blob = bucket.blob(filename)
#             blob.chunk_size = 10 * 1024 * 1024
            
#             blob.upload_from_string(video_data, content_type="video/mp4")
#             blob.make_public()
            
#             public_url = f"https://storage.googleapis.com/{self.bucket_name}/{filename}"
#             logger.info(f"📦 Video saved to bucket: {public_url}")
#             return public_url
            
#         except Exception as e:
#             logger.error(f"❌ Failed to save video to bucket: {e}")
#             return None

#     def generate_ad_video(
#         self,
#         product_name: str,
#         product_description: str,
#         platform: str,
#         duration: int = 6
#     ) -> Optional[str]:
#         """Generate a social media ad video"""
#         prompts = {
#             "tiktok": f"Product showcase of {product_name}. {product_description}. Modern style, 9:16 format.",
#             "instagram": f"Product showcase of {product_name}. {product_description}. Clean style, 9:16 format.",
#             "youtube": f"Product showcase of {product_name}. {product_description}. Professional style, 16:9 format."
#         }
        
#         prompt = prompts.get(platform, prompts["instagram"])
#         aspect_ratio = "9:16" if platform in ["tiktok", "instagram"] else "16:9"
        
#         if duration not in [4, 6, 8]:
#             duration = 6
        
#         return self.generate_video(
#             prompt=prompt,
#             duration=duration,
#             aspect_ratio=aspect_ratio
#         )

"""
Real AI Video Generation using Google's Gen AI SDK for Veo 3
Using the official preview model
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
        Generate a video using Veo 3 preview model
        """
        try:
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            logger.info(f"⏳ Generating video... (this will take 2-3 minutes)")
            
            # 🔥 FIX: Use preview model
            model_id = "veo-3.1-generate-preview"
            logger.info(f"📋 Using model: {model_id}")
            
            # Generate timestamp for output path
            timestamp = int(time.time())
            output_gcs_uri = f"gs://{self.bucket_name}/outputs/video_{timestamp}/"
            logger.info(f"📁 Output will be saved to: {output_gcs_uri}")
            
            # Start the generation operation
            operation = self.client.models.generate_videos(
                model=model_id,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    duration_seconds=duration,
                    output_gcs_uri=output_gcs_uri,
                ),
            )
            
            logger.info(f"📋 Operation ID: {operation.name}")
            logger.info("⏳ Polling for results (takes 2-3 minutes)...")
            
            # Wait for completion
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
            
            # Extract video URI
            if operation.result and operation.result.generated_videos:
                video_uri = operation.result.generated_videos[0].video.uri
                logger.info(f"✅ Success! Video saved to: {video_uri}")
                
                # Convert to public URL
                public_url = video_uri.replace("gs://", "https://storage.googleapis.com/")
                logger.info(f"📹 View here: {public_url}")
                
                # Make the file public
                self._make_file_public(video_uri)
                
                return public_url
            else:
                logger.warning("⚠️ Operation completed but no video was found.")
                return None
                
        except Exception as e:
            logger.error(f"❌ AI Generation Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _make_file_public(self, gcs_uri: str) -> bool:
        """Make a GCS file publicly accessible"""
        try:
            from google.cloud import storage
            
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            if len(parts) != 2:
                return False
            
            bucket_name, blob_name = parts
            
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.make_public()
            logger.info(f"✅ Made public: {blob.public_url}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Could not make file public: {e}")
            return False

    def generate_ad_video(
        self,
        product_name: str,
        product_description: str,
        platform: str,
        duration: int = 6
    ) -> Optional[str]:
        """Generate a social media ad video"""
        prompts = {
            "tiktok": f"Product showcase of {product_name}. {product_description}. Modern style, 9:16 format.",
            "instagram": f"Product showcase of {product_name}. {product_description}. Clean style, 9:16 format.",
            "youtube": f"Product showcase of {product_name}. {product_description}. Professional style, 16:9 format."
        }
        
        prompt = prompts.get(platform, prompts["instagram"])
        aspect_ratio = "9:16" if platform in ["tiktok", "instagram"] else "16:9"
        
        if duration not in [4, 6, 8]:
            duration = 6
        
        return self.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio
        )
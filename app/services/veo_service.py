"""
Optimized AI Video Generation using Google's Gen AI SDK for Veo 3
Lite/Fast version with cost optimization and faster generation
Supports: Text-to-Video, Image-to-Video, First/Last Frame
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from google import genai
from google.genai import types
from PIL import Image
import io

logger = logging.getLogger(__name__)

class VeoService:
    """Optimized Veo 3 service with Lite/Fast models for cost efficiency"""
    
    # Model pricing tiers (USD per second)
    MODEL_PRICING = {
        "veo-3.1-fast-generate-001": 0.12,    # ~₹10/sec - Best balance
        "veo-3.1-lite-generate-001": 0.05,    # ~₹4.25/sec - Cheapest
        "veo-3.1-generate-001": 0.40,         # ~₹34/sec - Premium (avoid)
    }
    
    def __init__(self, model: str = "fast"):
        """
        Initialize Veo 3 service with cost-optimized models
        
        Args:
            model: Model to use - "fast" (default) or "lite"
                  - fast: ~₹10/sec, good quality, 1080p, supports 10s
                  - lite: ~₹4.25/sec, acceptable quality, 720p, supports 8s
                  - premium: ~₹34/sec, highest quality, avoid for cost
        """
        self.project_id = "ai-social-ad-generator"
        self.location = "us-central1"
        self.bucket_name = "ai-ad-videos-kamlesh-2026"
        
        # Model mapping
        model_map = {
            "fast": "veo-3.1-fast-generate-001",
            "lite": "veo-3.1-lite-generate-001",
            "premium": "veo-3.1-generate-001"
        }
        
        self.model_type = model
        self.video_model = model_map.get(model, "veo-3.1-fast-generate-001")
        self.cost_per_sec = self.MODEL_PRICING.get(self.video_model, 0.12)
        
        logger.info(f"💰 Using model: {self.video_model} (₹{self.cost_per_sec * 85:.2f}/sec)")
        
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

    def _prepare_image(self, image: Union[str, Image.Image, bytes]) -> Optional[types.Image]:
        """
        Prepare image for API call with proper MIME type
        """
        try:
            if isinstance(image, str):
                # Check if it's a base64 string
                if image.startswith('data:image'):
                    # Extract MIME type and data
                    import base64
                    header, data = image.split(',', 1)
                    mime_type = header.split(':')[1].split(';')[0]
                    img_bytes = base64.b64decode(data)
                    return types.Image(
                        image_bytes=img_bytes,
                        mime_type=mime_type  # ✅ Set MIME type
                    )
                elif image.startswith(('http://', 'https://')):
                    # URL - download
                    import requests
                    response = requests.get(image)
                    img_bytes = response.content
                    # Determine MIME type from content-type header
                    mime_type = response.headers.get('content-type', 'image/png')
                    return types.Image(
                        image_bytes=img_bytes,
                        mime_type=mime_type
                    )
                else:
                    # Local file path
                    with open(image, 'rb') as f:
                        img_bytes = f.read()
                    # Determine MIME type from extension
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(image)
                    if not mime_type:
                        mime_type = 'image/png'
                    return types.Image(
                        image_bytes=img_bytes,
                        mime_type=mime_type
                    )
            elif isinstance(image, Image.Image):
                # PIL Image - save to bytes with proper format
                import io
                img_byte_arr = io.BytesIO()
                
                # Determine format from mode or use PNG
                if image.mode == 'RGB':
                    image.save(img_byte_arr, format='PNG')
                    mime_type = 'image/png'
                elif image.mode == 'RGBA':
                    image.save(img_byte_arr, format='PNG')
                    mime_type = 'image/png'
                elif image.mode == 'L':  # Grayscale
                    image.save(img_byte_arr, format='PNG')
                    mime_type = 'image/png'
                else:
                    image.save(img_byte_arr, format='JPEG')
                    mime_type = 'image/jpeg'
                
                return types.Image(
                    image_bytes=img_byte_arr.getvalue(),
                    mime_type=mime_type
                )
            elif isinstance(image, bytes):
                # Raw bytes - try to detect MIME type
                import imghdr
                # Check if it's a known image format
                img_type = imghdr.what(None, h=image)
                mime_types = {
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'webp': 'image/webp',
                    'bmp': 'image/bmp'
                }
                mime_type = mime_types.get(img_type, 'image/png')
                return types.Image(
                    image_bytes=image,
                    mime_type=mime_type
                )
            else:
                logger.error(f"❌ Unsupported image type: {type(image)}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to prepare image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_video(
        self, 
        prompt: str, 
        duration: int = 6, 
        aspect_ratio: str = "16:9",
        resolution: str = None,
        enhance_prompt: bool = True,
        generate_audio: bool = True,
        max_wait_time: int = 180,
        image: Optional[Union[str, Image.Image, bytes]] = None,
        last_frame: Optional[Union[str, Image.Image, bytes]] = None
    ) -> Optional[str]:
        """
        Generate a video using optimized Veo 3 model
        
        Args:
            prompt: Text description of the video
            duration: Length in seconds (4, 6, 8, or 10 for fast models)
            aspect_ratio: "16:9", "9:16", or "1:1"
            resolution: "1080p" (fast) or "720p" (lite)
            enhance_prompt: Whether to enhance the prompt
            generate_audio: Whether to generate audio
            max_wait_time: Maximum wait time in seconds
            image: Starting image for image-to-video or first frame
            last_frame: Ending image for first/last frame feature
        
        Returns:
            Public URL of the generated video
        """
        # Auto-set resolution based on model
        if resolution is None:
            resolution = "720p" if "lite" in self.video_model else "1080p"
        
        # Duration limits for different models
        max_duration = 10 if "fast" in self.video_model else 8
        if duration > max_duration:
            logger.warning(f"⚠️ Model supports max {max_duration}s, adjusting from {duration}s")
            duration = max_duration
        
        try:
            # Calculate estimated cost
            estimated_cost = duration * self.cost_per_sec * 85  # INR
            logger.info(f"💰 Estimated cost: ₹{estimated_cost:.2f} for {duration}s video")
            
            # Log what's being generated
            if image and last_frame:
                logger.info(f"🎬 Generating with FIRST and LAST frame images")
            elif image:
                logger.info(f"🎬 Generating IMAGE-TO-VIDEO from reference image")
            else:
                logger.info(f"🎬 Generating TEXT-TO-VIDEO")
            
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            logger.info(f"⚡ Generating with {self.video_model}...")
            
            timestamp = int(time.time())
            model_prefix = self.video_model.split('-')[2] if len(self.video_model.split('-')) > 2 else "veo"
            output_gcs_uri = f"gs://{self.bucket_name}/generated/{model_prefix}_{timestamp}/"
            
            # Prepare config
            config_kwargs = {
                "aspect_ratio": aspect_ratio,
                "number_of_videos": 1,
                "duration_seconds": duration,
                "resolution": resolution,
                "person_generation": "allow_adult",
                "enhance_prompt": enhance_prompt,
                "generate_audio": generate_audio,
                "output_gcs_uri": output_gcs_uri,
            }
            
            # Prepare for image-to-video or first/last frame
            image_obj = None
            last_frame_obj = None
            
            if image:
                image_obj = self._prepare_image(image)
                if not image_obj:
                    logger.error("❌ Failed to prepare image")
                    return None
            
            if last_frame:
                last_frame_obj = self._prepare_image(last_frame)
                if not last_frame_obj:
                    logger.error("❌ Failed to prepare last frame")
                    return None
            
            # Start generation with appropriate parameters
            if image_obj and last_frame_obj:
                # First/Last Frame - full control
                config = types.GenerateVideosConfig(**config_kwargs)
                operation = self.client.models.generate_videos(
                    model=self.video_model,
                    prompt=prompt,
                    image=image_obj,
                    config=types.GenerateVideosConfig(
                        **config_kwargs,
                        last_frame=last_frame_obj,
                    ),
                )
            elif image_obj:
                # Image-to-Video
                operation = self.client.models.generate_videos(
                    model=self.video_model,
                    prompt=prompt,
                    image=image_obj,
                    config=types.GenerateVideosConfig(**config_kwargs),
                )
            else:
                # Text-to-Video
                operation = self.client.models.generate_videos(
                    model=self.video_model,
                    prompt=prompt,
                    config=types.GenerateVideosConfig(**config_kwargs),
                )
            
            logger.info(f"📋 Operation: {operation.name}")
            
            # Wait with progress updates
            start_time = time.time()
            poll_interval = 5
            
            while not operation.done:
                elapsed = int(time.time() - start_time)
                
                if elapsed > max_wait_time:
                    logger.error(f"❌ Generation timed out after {max_wait_time}s")
                    return None
                
                if elapsed % 15 == 0 and elapsed > 0:
                    logger.info(f"⏳ Generating... ({elapsed}s elapsed)")
                
                time.sleep(poll_interval)
                operation = self.client.operations.get(operation)
            
            logger.info(f"✅ Generated in {int(time.time() - start_time)}s")
            
            # Check for errors
            if operation.error:
                logger.error(f"❌ Operation error: {operation.error}")
                return None
            
            # Extract video URL
            if operation.result and operation.result.generated_videos:
                video_obj = operation.result.generated_videos[0]
                
                if hasattr(video_obj, 'video') and hasattr(video_obj.video, 'uri'):
                    video_uri = video_obj.video.uri
                    logger.info(f"✅ Video ready: {video_uri}")
                    
                    if video_uri.startswith("gs://"):
                        public_url = video_uri.replace("gs://", "https://storage.googleapis.com/")
                        return public_url
                    return video_uri
            
            logger.error("❌ No video in response")
            return None
            
        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_ad_video(
        self,
        product_name: str,
        product_description: str,
        platform: str,
        duration: int = 6,
        use_lite: bool = False,
        product_image: Optional[Union[str, Image.Image, bytes]] = None,
        use_last_frame: bool = False
    ) -> Optional[str]:
        """
        Generate a social media ad video with cost optimization
        
        Args:
            product_name: Name of the product
            product_description: Description of the product
            platform: Target platform (tiktok, instagram, youtube)
            duration: Video length (4, 6, 8, or 10)
            use_lite: Use lite model for even cheaper generation
            product_image: Product image to use as starting frame
            use_last_frame: If True, use the product image as both first and last frame
        
        Returns:
            Public URL of the generated video
        """
        # Switch model if requested
        if use_lite and "fast" in self.video_model:
            self.video_model = "veo-3.1-lite-generate-001"
            self.cost_per_sec = self.MODEL_PRICING.get(self.video_model, 0.05)
            logger.info(f"💰 Switched to Lite model: ₹{self.cost_per_sec * 85:.2f}/sec")
        
        # Platform-specific prompts
        prompts = {
            "tiktok": f"Product showcase of {product_name}. {product_description}. Modern style, fast-paced, 9:16 format, vibrant colors, TikTok style.",
            "instagram": f"Product showcase of {product_name}. {product_description}. Clean style, aesthetic, 9:16 format, Instagram Reel style.",
            "youtube": f"Product showcase of {product_name}. {product_description}. Professional style, cinematic, 16:9 format, YouTube ad style."
        }
        
        prompt = prompts.get(platform, prompts["instagram"])
        aspect_ratio = "9:16" if platform in ["tiktok", "instagram"] else "16:9"
        
        # Duration limits
        max_duration = 10 if "fast" in self.video_model else 8
        if duration > max_duration:
            duration = max_duration
        
        # Estimate cost
        est_cost = duration * self.cost_per_sec * 85
        logger.info(f"📊 Estimated cost: ₹{est_cost:.2f} for {duration}s {platform} ad")
        
        # Prepare image for ad
        last_frame_img = product_image if use_last_frame else None
        first_frame_img = product_image if product_image else None
        
        return self.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution="1080p" if "fast" in self.video_model else "720p",
            enhance_prompt=True,
            generate_audio=True,
            max_wait_time=180,
            image=first_frame_img,
            last_frame=last_frame_img
        )

    def generate_from_image(
        self,
        prompt: str,
        image: Union[str, Image.Image, bytes],
        duration: int = 6,
        aspect_ratio: str = "9:16",
        generate_audio: bool = True,
        use_lite: bool = False
    ) -> Optional[str]:
        """
        Generate video from a reference image (Image-to-Video)
        
        Args:
            prompt: Text description of the video
            image: Reference image (path, PIL Image, or bytes)
            duration: Length in seconds
            aspect_ratio: "16:9", "9:16", or "1:1"
            generate_audio: Whether to generate audio
            use_lite: Use lite model for cheaper generation
        
        Returns:
            Public URL of the generated video
        """
        if use_lite and "fast" in self.video_model:
            self.video_model = "veo-3.1-lite-generate-001"
            self.cost_per_sec = self.MODEL_PRICING.get(self.video_model, 0.05)
            logger.info(f"💰 Switched to Lite model: ₹{self.cost_per_sec * 85:.2f}/sec")
        
        return self.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution="1080p" if "fast" in self.video_model else "720p",
            enhance_prompt=True,
            generate_audio=generate_audio,
            image=image,
            last_frame=None
        )

    def generate_with_first_last_frame(
        self,
        prompt: str,
        first_frame: Union[str, Image.Image, bytes],
        last_frame: Union[str, Image.Image, bytes],
        duration: int = 6,
        aspect_ratio: str = "9:16",
        generate_audio: bool = True,
        use_lite: bool = False
    ) -> Optional[str]:
        """
        Generate video with first and last frame control
        
        Args:
            prompt: Text description of the transition
            first_frame: Starting image
            last_frame: Ending image
            duration: Length in seconds (4, 6, or 8)
            aspect_ratio: "16:9", "9:16", or "1:1"
            generate_audio: Whether to generate audio
            use_lite: Use lite model for cheaper generation
        
        Returns:
            Public URL of the generated video
        """
        if use_lite and "fast" in self.video_model:
            self.video_model = "veo-3.1-lite-generate-001"
            self.cost_per_sec = self.MODEL_PRICING.get(self.video_model, 0.05)
            logger.info(f"💰 Switched to Lite model: ₹{self.cost_per_sec * 85:.2f}/sec")
        
        # First/Last frame supports up to 8 seconds
        if duration > 8:
            logger.warning(f"⚠️ First/Last frame supports max 8s, adjusting from {duration}s")
            duration = 8
        
        return self.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution="1080p" if "fast" in self.video_model else "720p",
            enhance_prompt=True,
            generate_audio=generate_audio,
            image=first_frame,
            last_frame=last_frame
        )

    def get_cost_estimate(self, duration: int = 6, use_lite: bool = False) -> Dict[str, Any]:
        """Get cost estimate for video generation"""
        model = "veo-3.1-lite-generate-001" if use_lite else "veo-3.1-fast-generate-001"
        cost_per_sec = self.MODEL_PRICING.get(model, 0.12)
        
        return {
            "model": model,
            "duration_seconds": duration,
            "cost_usd": round(duration * cost_per_sec, 2),
            "cost_inr": round(duration * cost_per_sec * 85, 2),
            "supports_audio": True,
            "max_resolution": "720p" if "lite" in model else "1080p",
            "max_duration": "8s" if "lite" in model else "10s",
            "supports_image_to_video": True,
            "supports_first_last_frame": True
        }


# ===== USAGE EXAMPLES =====

def example_usage():
    """Example usage of the optimized Veo service"""
    
    # Initialize with Fast model (recommended)
    veo = VeoService(model="fast")
    
    # ===== 1. Text-to-Video (Original) =====
    print("\n" + "="*50)
    print("1. TEXT-TO-VIDEO (Original)")
    print("="*50)
    video_url = veo.generate_ad_video(
        product_name="Premium Wireless Earbuds",
        product_description="Active noise cancellation, 24-hour battery life, crystal-clear sound",
        platform="instagram",
        duration=8
    )
    if video_url:
        print(f"✅ Video: {video_url}")
    
    # ===== 2. Image-to-Video =====
    print("\n" + "="*50)
    print("2. IMAGE-TO-VIDEO (From product image)")
    print("="*50)
    # product_image = "path/to/product.jpg"  # Your product image path
    # video_url = veo.generate_from_image(
    #     prompt="Product floating in elegant space with soft lighting, cinematic quality",
    #     image=product_image,
    #     duration=6,
    #     aspect_ratio="9:16"
    # )
    # if video_url:
    #     print(f"✅ Video: {video_url}")
    
    # ===== 3. First/Last Frame =====
    print("\n" + "="*50)
    print("3. FIRST/LAST FRAME (Full control)")
    print("="*50)
    # first_image = "path/to/box_closed.jpg"
    # last_image = "path/to/product_showcase.jpg"
    # video_url = veo.generate_with_first_last_frame(
    #     prompt="Transition from closed product box to product showcase with smooth animation",
    #     first_frame=first_image,
    #     last_frame=last_image,
    #     duration=6,
    #     aspect_ratio="9:16"
    # )
    # if video_url:
    #     print(f"✅ Video: {video_url}")
    
    # ===== 4. Ad with Product Image =====
    print("\n" + "="*50)
    print("4. AD GENERATION WITH PRODUCT IMAGE")
    print("="*50)
    # video_url = veo.generate_ad_video(
    #     product_name="Premium Wireless Earbuds",
    #     product_description="Active noise cancellation, 24-hour battery life, crystal-clear sound",
    #     platform="instagram",
    #     duration=6,
    #     product_image=product_image,  # Use product image as first frame
    #     use_last_frame=False
    # )
    # if video_url:
    #     print(f"✅ Video: {video_url}")
    
    # ===== 5. Cost Estimate =====
    print("\n" + "="*50)
    print("5. COST ESTIMATES")
    print("="*50)
    for duration in [4, 6, 8]:
        est_fast = veo.get_cost_estimate(duration=duration, use_lite=False)
        est_lite = veo.get_cost_estimate(duration=duration, use_lite=True)
        print(f"\n{duration}s Video:")
        print(f"  Fast: ₹{est_fast['cost_inr']:.2f} (1080p)")
        print(f"  Lite: ₹{est_lite['cost_inr']:.2f} (720p)")
    
    # ===== 6. Feature Summary =====
    print("\n" + "="*50)
    print("6. FEATURE SUMMARY")
    print("="*50)
    print(f"✅ Model: {veo.video_model}")
    print(f"✅ Cost/sec: ₹{veo.cost_per_sec * 85:.2f}")
    print(f"✅ Supports Audio: Yes")
    print(f"✅ Supports Image-to-Video: Yes")
    print(f"✅ Supports First/Last Frame: Yes (max 8s)")
    print(f"✅ Max Duration: {'10s' if 'fast' in veo.video_model else '8s'}")


if __name__ == "__main__":
    example_usage()
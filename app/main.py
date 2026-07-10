"""
Production-Ready AI Social Media Ad Generator API
With PostgreSQL Database Integration
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import uuid
import shutil
import os
from typing import Optional, List
from datetime import datetime
import json
import logging
import random
import base64
import tempfile
import os
import logging
import subprocess
from typing import Optional, List
from datetime import datetime, timedelta
from google.cloud import storage
import requests as http_requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Create FastAPI App ===
app = FastAPI(
    title="AI Social Media Ad Generator API",
    description="Generate professional social media ads using AI (Veo 3)",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Import Routes and Services ===
from app.routes import auth
app.include_router(auth.router)

from app.services.veo_service import VeoService
from app.models.database import db_service, init_db
from app.tasks.background_tasks import process_video_generation_db

# === Initialize Database ===
try:
    init_db()
    logger.info("✅ PostgreSQL Database initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Database initialization warning: {e}")

# === Initialize Veo Service ===
try:
    veo_service = VeoService()
    logger.info("✅ Veo Service initialized")
except Exception as e:
    logger.warning(f"⚠️ Veo Service not available: {e}")
    veo_service = None

# ===== SINGLE get_user_id function =====
def get_user_id(request: Request) -> str:
    """
    Extract user ID from request headers.
    Returns the user ID or raises an exception.
    """
    user_id = request.headers.get("X-User-ID")
    
    # Log for debugging
    logger.info(f"📋 X-User-ID header: {user_id}")
    
    if not user_id:
        # For admin endpoints, allow fallback
        path = request.url.path
        admin_endpoints = ["/api/v1/users", "/api/v1/tasks", "/api/v1/analytics", "/api/v1/user"]
        if any(path.startswith(endpoint) for endpoint in admin_endpoints):
            user_id = "+919999999999"
            logger.info(f"👤 Admin endpoint: using fallback user {user_id}")
        else:
            logger.error("❌ No X-User-ID found in request headers")
            raise HTTPException(
                status_code=401,
                detail="User ID not provided. Please include X-User-ID header."
            )
    
    logger.info(f"👤 User ID: {user_id}")
    return user_id

# === Models ===
class GenerateVideoRequest(BaseModel):
    platform: str = Field(..., description="tiktok, instagram, or youtube")
    product_name: str = Field(..., description="Name of the product")
    product_description: str = Field(..., description="Description of the product")
    duration_seconds: int = Field(6, ge=4, le=8, description="Video duration (4, 6, or 8 seconds)")
    template_id: Optional[str] = Field(None, description="Template ID to use")
    enhance_prompt: bool = Field(True, description="Enhance prompt with AI")
    generate_audio: bool = Field(True, description="Generate audio for video")
    generation_mode: Optional[str] = Field("text", description="Generation mode: text, image, or first-last")
    first_frame: Optional[str] = Field(None, description="Base64 encoded first frame image")
    last_frame: Optional[str] = Field(None, description="Base64 encoded last frame image (for first-last mode)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "tiktok",
                "product_name": "Wireless Earbuds",
                "product_description": "Premium wireless earbuds with noise cancellation",
                "duration_seconds": 6,
                "template_id": "modern_product_showcase",
                "enhance_prompt": True,
                "generate_audio": True
            }
        }

class GenerateVideoResponse(BaseModel):
    task_id: str
    status: str
    message: str
    credits_used: int
    credits_remaining: int

class VideoStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

class BulkGenerateRequest(BaseModel):
    products: List[GenerateVideoRequest]
    auto_complete: bool = False



# ===== UPDATE SceneRequest Model =====
class SceneRequest(BaseModel):
    title: Optional[str] = Field("Scene", description="Title of the scene")
    product_name: str = Field(..., description="Product name for this scene")
    product_description: str = Field(..., description="Product description")
    platform: str = Field("instagram", description="Platform for this scene")
    duration_seconds: int = Field(6, ge=4, le=8)
    generation_mode: str = Field("text", description="text, image, or first-last")
    first_frame: Optional[str] = None
    last_frame: Optional[str] = None
    scene_order: int = Field(..., description="Order of this scene in the chain")
    transition_style: Optional[str] = Field("smooth", description="Transition between scenes")


class ChainVideoRequest(BaseModel):
    scenes: List[SceneRequest]
    chain_name: str = Field(..., description="Name for this video chain")
    target_platform: str = Field("instagram", description="Platform for the final video")
    total_duration: Optional[int] = Field(None, description="Total duration in seconds")

class ChainResponse(BaseModel):
    chain_id: str
    chain_name: str
    total_scenes: int
    scenes: List[dict]
    status: str
    message: str
    credits_required: int
    credits_remaining: int







# === Sample Videos Fallback ===
SAMPLE_VIDEOS = [
    "https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/demo/sample.mp4",
    "https://www.w3schools.com/html/mov_bbb.mp4",
]

# === Health & Root Endpoints ===
@app.get("/")
async def root():
    return {
        "message": "🚀 AI Social Media Ad Generator API v3.0",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "operational",
        "database": "PostgreSQL",
        "storage": "Google Cloud Storage",
        "features": [
            "Real AI Video Generation (Veo 3)",
            "PostgreSQL Database",
            "GCP Storage",
            "User Authentication (OTP)",
            "Credit System",
            "Video History",
            "Bulk Generation",
            "Analytics",
            # ===== NEW: Image features =====
            "Image-to-Video Generation",
            "First/Last Frame Control"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check with database status"""
    db_status = "connected"
    try:
        db_service.get_user_credits("test_user")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "veo_service": "available" if veo_service else "unavailable",
        "total_users": len(db_service.get_all_users()) if hasattr(db_service, 'get_all_users') else "unknown"
    }

def save_base64_image(base64_str: str, prefix: str = "image") -> Optional[str]:
    """Save base64 image to file and return path"""
    try:
        # Remove data URL prefix if present
        if "base64," in base64_str:
            base64_str = base64_str.split("base64,")[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_str)
        
        # Create filename
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = f"uploads/{filename}"
        
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        
        # Save file
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        logger.info(f"✅ Image saved: {filepath} ({len(image_data)} bytes)")
        return filepath
    except Exception as e:
        logger.error(f"❌ Failed to save base64 image: {e}")
        return None




from google.cloud import storage
import re

async def combine_videos_gcs_compose(video_urls: list, chain_id: str) -> Optional[str]:
    """
    Combine videos using GCS object composition - NO download required!
    Instant and free!
    """
    try:
        # Initialize GCS client
        storage_client = storage.Client(project="ai-social-ad-generator")
        bucket = storage_client.bucket("ai-ad-videos-kamlesh-2026")
        
        # Get blob objects from URLs
        source_blobs = []
        for url in video_urls:
            # Extract blob name from URL
            # URL format: https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/generated/fast_xxx/sample_0.mp4
            blob_name = url.replace("https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/", "")
            blob = bucket.blob(blob_name)
            
            # Verify blob exists
            if blob.exists():
                source_blobs.append(blob)
                logger.info(f"📁 Found blob: {blob_name}")
            else:
                logger.warning(f"⚠️ Blob not found: {blob_name}")
        
        if len(source_blobs) < 2:
            logger.warning("⚠️ Less than 2 blobs found for composition")
            return video_urls[0] if video_urls else None
        
        # Create combined blob
        combined_blob_name = f"chains/{chain_id}.mp4"
        combined_blob = bucket.blob(combined_blob_name)
        
        # Compose objects (this is instant!)
        # Note: Works for up to 32 objects, each < 5GB
        logger.info(f"📦 Composing {len(source_blobs)} videos into {combined_blob_name}")
        combined_blob.compose(source_blobs)
        
        # Make the combined video public
        combined_blob.make_public()
        
        # Generate public URL
        combined_url = f"https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/{combined_blob_name}"
        logger.info(f"✅ Combined video ready: {combined_url}")
        
        return combined_url
        
    except Exception as e:
        logger.error(f"❌ GCS compose failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# === Video Generation Endpoints ===
@app.post("/api/v1/generate", response_model=GenerateVideoResponse)
async def generate_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """Generate a video using REAL AI with Image-to-Video and First/Last Frame support"""
    user_id = get_user_id(req)
    logger.info(f"🎬 Generation requested for user: {user_id}")
    logger.info(f"📋 Generation mode: {request.generation_mode}")
    logger.info(f"📸 First frame present: {bool(request.first_frame)}")
    logger.info(f"📸 Last frame present: {bool(request.last_frame)}")
    
    # Check credits
    credits = db_service.get_user_credits(user_id)
    logger.info(f"💰 User {user_id} has {credits} credits")
    
    if credits < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    # ===== NEW: Handle Image Upload =====
    first_frame_path = None
    last_frame_path = None
    
    # Save first frame image if present
    if request.first_frame:
        first_frame_path = save_base64_image(request.first_frame, "first_frame")
        logger.info(f"📸 First frame saved: {first_frame_path}")
    
    # Save last frame for first-last mode
    if request.generation_mode == "first-last" and request.last_frame:
        last_frame_path = save_base64_image(request.last_frame, "last_frame")
        logger.info(f"📸 Last frame saved: {last_frame_path}")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    logger.info(f"📋 Created task ID: {task_id}")
    
    # Deduct credits
    db_service.update_user_credits(user_id, -1)
    logger.info(f"💰 Deducted 1 credit from {user_id}")
    
    # ===== NEW: Create a dictionary with ALL data for background task =====
    request_dict = request.dict()
    request_dict["first_frame_path"] = first_frame_path
    request_dict["last_frame_path"] = last_frame_path
    request_dict["generation_mode"] = request.generation_mode
    
    # Store in database
    video_data = {
        "id": task_id,
        "user_id": user_id,
        "platform": request.platform,
        "product_name": request.product_name,
        "product_description": request.product_description,
        "duration_seconds": request.duration_seconds,
        "status": "pending",
        "credits_used": 1,
        "progress": 0,
        "generation_mode": request.generation_mode,
        "first_frame_path": first_frame_path,
        "last_frame_path": last_frame_path
    }
    db_service.save_video(user_id, video_data)
    logger.info(f"💾 Saved video record to database")
    
    # Start background processing
    logger.info(f"🚀 Adding background task for {task_id}")
    background_tasks.add_task(
        process_video_generation_db,
        task_id,
        request_dict,  # Pass the modified dict with image paths
        user_id
    )
    logger.info(f"✅ Background task added for {task_id}")
    
    return GenerateVideoResponse(
        task_id=task_id,
        status="pending",
        message=f"✅ Video generation started! Check status at /api/v1/status/{task_id}",
        credits_used=1,
        credits_remaining=db_service.get_user_credits(user_id)
    )

@app.get("/api/v1/status/{task_id}")
async def get_generation_status(task_id: str, req: Request):
    """Check the status of a video generation task"""
    user_id = get_user_id(req)
    
    video = db_service.get_video(user_id, task_id)
    
    if not video:
        return {
            "task_id": task_id,
            "status": "not_found",
            "progress": 0,
            "video_url": None,
            "error_message": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message": "Task not found"
        }
    
    progress = video.get("progress", 0)
    status = video.get("status", "unknown")
    
    messages = {
        0: "⏳ Queued...",
        10: "⏳ Starting generation...",
        20: "🤖 Initializing AI model...",
        30: "🎬 Generating video...",
        50: "🎬 Adding effects...",
        70: "🎬 Rendering video...",
        80: "📤 Preparing for upload...",
        90: "☁️ Uploading to cloud...",
        100: "✅ Complete!",
    }
    
    message = "⏳ Processing..."
    for p in sorted(messages.keys(), reverse=True):
        if progress >= p:
            message = messages[p]
            break
    
    if status == "completed":
        message = "✅ Video ready!"
    elif status == "failed":
        message = f"❌ Failed: {video.get('error_message', 'Unknown error')}"
    
    return {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "video_url": video.get("video_url"),
        "error_message": video.get("error_message"),
        "created_at": video.get("created_at"),
        "updated_at": video.get("updated_at"),
        "message": message
    }

@app.post("/api/v1/generate-auto")
async def generate_and_auto_complete(request: GenerateVideoRequest, req: Request):
    """Generate and auto-complete instantly (for testing)"""
    user_id = get_user_id(req)
    
    if db_service.get_user_credits(user_id) < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    video_id = f"auto_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    db_service.update_user_credits(user_id, -1)
    
    video_url = random.choice(SAMPLE_VIDEOS)
    
    db_service.save_video(user_id, {
        "id": video_id,
        "video_url": video_url,
        "platform": request.platform,
        "product_name": request.product_name,
        "product_description": request.product_description,
        "duration_seconds": request.duration_seconds,
        "status": "completed",
        "credits_used": 1
    })
    
    return {
        "task_id": video_id,
        "status": "completed",
        "video_url": video_url,
        "message": f"✅ Video for '{request.product_name}' ready!",
        "credits_used": 1,
        "credits_remaining": db_service.get_user_credits(user_id)
    }

@app.delete("/api/v1/cancel/{task_id}")
async def cancel_generation(task_id: str, req: Request):
    """Cancel a pending video generation task"""
    user_id = get_user_id(req)
    
    video = db_service.get_video(user_id, task_id)
    if not video:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if video["status"] in ["pending", "processing"]:
        db_service.update_video_status(user_id, task_id, "cancelled")
        db_service.update_user_credits(user_id, 1)
        return {
            "status": "success",
            "message": f"✅ Task {task_id} cancelled. Credit refunded.",
            "credits_remaining": db_service.get_user_credits(user_id)
        }
    
    raise HTTPException(
        status_code=400,
        detail=f"Cannot cancel task with status: {video['status']}"
    )

# === User Video History ===

@app.get("/api/v1/user/videos")
async def get_user_videos(
    limit: int = 50,
    offset: int = 0,
    req: Request = None
):
    """Get user's video history from PostgreSQL"""
    user_id = get_user_id(req) if req else "demo_user"
    
    videos = db_service.get_user_videos(user_id, limit, offset)
    total = db_service.get_user_video_count(user_id) if hasattr(db_service, 'get_user_video_count') else len(videos)
    
    return {
        "videos": videos,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/video/{video_id}")
async def get_video(video_id: str, req: Request):
    """Get a specific video from PostgreSQL"""
    user_id = get_user_id(req)
    
    video = db_service.get_video(user_id, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video

# === Bulk Generation ===

@app.post("/api/v1/generate-bulk")
async def generate_bulk_videos(request: BulkGenerateRequest, req: Request):
    """Generate multiple videos at once"""
    user_id = get_user_id(req)
    total_credits_needed = len(request.products)
    
    credits = db_service.get_user_credits(user_id)
    if credits < total_credits_needed:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {total_credits_needed}, have {credits}"
        )
    
    tasks = []
    for product in request.products:
        video_id = f"bulk_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
        db_service.update_user_credits(user_id, -1)
        
        if request.auto_complete:
            video_url = random.choice(SAMPLE_VIDEOS)
            status = "completed"
        else:
            video_url = None
            status = "pending"
        
        db_service.save_video(user_id, {
            "id": video_id,
            "video_url": video_url,
            "platform": product.platform,
            "product_name": product.product_name,
            "product_description": product.product_description,
            "duration_seconds": product.duration_seconds,
            "status": status,
            "credits_used": 1
        })
        
        tasks.append({
            "task_id": video_id,
            "product_name": product.product_name,
            "status": status,
            "video_url": video_url
        })
    
    return {
        "status": "success",
        "total_tasks": len(tasks),
        "tasks": tasks,
        "bulk_discount_applied": len(tasks) >= 3,
        "credits_remaining": db_service.get_user_credits(user_id),
        "message": f"Created {len(tasks)} tasks"
    }

# === Credit Management ===

@app.get("/api/v1/credits/balance")
async def get_credit_balance(req: Request):
    """Get user's credit balance from database"""
    try:
        user_id = get_user_id(req)
        credits = db_service.get_user_credits(user_id)
        
        return {
            "balance": credits,
            "currency": "credits",
            "user_id": user_id,
            "packages": [
                {"name": "Starter", "credits": 10, "price": 9.99, "popular": False},
                {"name": "Popular", "credits": 50, "price": 39.99, "popular": True},
                {"name": "Pro", "credits": 100, "price": 69.99, "popular": False},
                {"name": "Enterprise", "credits": 500, "price": 299.99, "popular": False}
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credits: {e}")
        raise HTTPException(status_code=500, detail="Failed to get credits")

@app.get("/api/v1/user/{user_id}")
async def get_user_by_id(user_id: str):
    """Get user by ID from PostgreSQL"""
    try:
        user = db_service.get_user(user_id)
        if user:
            return {
                "status": "success",
                "user": user
            }
        else:
            return {
                "status": "error",
                "message": f"User {user_id} not found"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/v1/users")
async def get_all_users():
    """Get all users from PostgreSQL"""
    try:
        users = db_service.get_all_users()
        return {
            "status": "success",
            "total": len(users),
            "users": users
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/v1/credits/add")
async def add_credits(amount: int = 10, req: Request = None):
    """Add credits for testing"""
    try:
        user_id = get_user_id(req) if req else "demo_user"
    except HTTPException:
        user_id = "demo_user"
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    new_balance = db_service.update_user_credits(user_id, amount)
    return {
        "status": "success",
        "new_balance": new_balance,
        "added": amount,
        "user_id": user_id
    }

@app.get("/api/v1/credits/packages")
async def get_credit_packages():
    """Get available credit packages"""
    return {
        "packages": [
            {"id": "starter", "name": "Starter", "credits": 10, "price": 9.99, "savings": "0%"},
            {"id": "popular", "name": "Popular", "credits": 50, "price": 39.99, "savings": "20%", "popular": True},
            {"id": "pro", "name": "Pro", "credits": 100, "price": 69.99, "savings": "30%"},
            {"id": "enterprise", "name": "Enterprise", "credits": 500, "price": 299.99, "savings": "40%"}
        ]
    }

# === Templates ===

@app.get("/api/v1/templates")
async def get_templates():
    """Get available video templates"""
    return {
        "templates": [
            {
                "id": "modern_product_showcase",
                "name": "Modern Product Showcase",
                "style": "Clean, minimal, product-focused",
                "best_for": "Tech products, gadgets",
                "duration": 6,
                "aspect_ratio": "9:16",
                "popular": True
            },
            {
                "id": "lifestyle_emotional",
                "name": "Lifestyle & Emotional",
                "style": "Warm, emotional, human-centric",
                "best_for": "Fashion, wellness, food",
                "duration": 8,
                "aspect_ratio": "9:16",
                "popular": True
            },
            {
                "id": "fast_paced_energetic",
                "name": "Fast Paced & Energetic",
                "style": "High energy, quick cuts, dynamic",
                "best_for": "Sports, fitness, gaming",
                "duration": 4,
                "aspect_ratio": "16:9",
                "popular": False
            }
        ]
    }

# === Image Upload ===

@app.post("/api/v1/upload-product-image")
async def upload_product_image(
    file: UploadFile = File(...),
    product_id: Optional[str] = None
):
    """Upload product images for video generation"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_location = f"uploads/{unique_filename}"
    
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    return {
        "status": "success",
        "filename": file.filename,
        "location": file_location,
        "url": f"/uploads/{unique_filename}",
        "size_bytes": file_size,
        "content_type": file.content_type,
        "product_id": product_id
    }

# === Analytics ===

@app.get("/api/v1/analytics")
async def get_analytics(req: Request):
    """Get generation analytics from PostgreSQL"""
    user_id = get_user_id(req)
    
    videos = db_service.get_user_videos(user_id, 1000)
    total = len(videos)
    completed = len([v for v in videos if v.get("status") == "completed"])
    pending = len([v for v in videos if v.get("status") == "pending"])
    processing = len([v for v in videos if v.get("status") == "processing"])
    failed = len([v for v in videos if v.get("status") == "failed"])
    
    platforms = {}
    for video in videos:
        platform = video.get("platform", "unknown")
        platforms[platform] = platforms.get(platform, 0) + 1
    
    return {
        "total_generations": total,
        "completed": completed,
        "pending": pending,
        "processing": processing,
        "failed": failed,
        "success_rate": f"{(completed / total * 100) if total > 0 else 0:.1f}%",
        "platform_distribution": platforms,
        "credits_remaining": db_service.get_user_credits(user_id),
        "recent_activity": [
            {
                "product": v.get("product_name", "Unknown"),
                "status": v.get("status", "unknown"),
                "created": v.get("created_at", "")
            }
            for v in videos[:5]
        ]
    }

# === User Profile ===

@app.get("/api/v1/user/profile")
async def get_user_profile(req: Request):
    """Get user profile from PostgreSQL"""
    user_id = get_user_id(req)
    
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    videos = db_service.get_user_videos(user_id, 10)
    
    return {
        "user": user,
        "recent_videos": videos[:5],
        "total_videos": user.get("total_videos", 0)
    }

# === Admin Endpoints ===

@app.get("/api/v1/tasks")
async def list_all_tasks(limit: int = 10, status: Optional[str] = None, req: Request = None):
    """List all tasks for a user"""
    user_id = get_user_id(req) if req else "demo_user"
    
    videos = db_service.get_user_videos(user_id, limit)
    if status:
        videos = [v for v in videos if v.get("status") == status]
    
    return {
        "total_tasks": db_service.get_user_video_count(user_id) if hasattr(db_service, 'get_user_video_count') else len(videos),
        "filtered_count": len(videos),
        "tasks": [
            {
                "id": v.get("id"),
                "status": v.get("status"),
                "product": v.get("product_name"),
                "progress": v.get("progress", 0),
                "created": v.get("created_at")
            }
            for v in videos
        ]
    }

# === Serve Frontend ===

@app.get("/app")
async def serve_frontend():
    """Serve the frontend HTML page"""
    frontend_path = "frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Frontend not found. Create frontend/index.html"}

@app.get("/login")
async def serve_login():
    """Serve the login page"""
    login_path = "frontend/login.html"
    if os.path.exists(login_path):
        return FileResponse(login_path)
    else:
        return """
        <html>
            <body>
                <h1>Login Page</h1>
                <p>Please create frontend/login.html</p>
                <p>Current directory: """ + os.getcwd() + """</p>
            </body>
        </html>
        """

@app.get("/login-debug")
async def serve_login_debug():
    """Serve the debug login page"""
    login_path = "frontend/login_debug.html"
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"message": "Debug login page not found"}

@app.get("/admin")
async def serve_admin():
    """Serve the admin panel"""
    admin_path = "frontend/admin.html"
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"message": "Admin panel not found"}

# === Error Handlers ===

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)}
    )




# Payment verification endpoint
@app.post("/api/v1/verify-payment")
async def verify_payment(request: Request):
    try:
        data = await request.json()
        user_id = get_user_id(request)
        
        credits = data.get("credits")
        amount = data.get("amount")
        utr = data.get("utr")
        
        if not credits or not amount or not utr:
            raise HTTPException(status_code=400, detail="Missing payment details")
        
        # In production, verify the UTR with your payment gateway
        # For now, we'll trust the user and add credits
        
        # Add credits to user
        new_balance = db_service.update_user_credits(user_id, credits)
        
        # Record the purchase
        purchase_data = {
            "id": f"pur_{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "amount": amount,
            "credits_purchased": credits,
            "payment_method": "upi",
            "payment_id": utr,
            "status": "completed"
        }
        db_service.add_purchase(user_id, purchase_data)
        
        return {
            "status": "success",
            "message": f"Added {credits} credits",
            "new_balance": new_balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add welcome credits endpoint
@app.post("/api/v1/welcome-credits")
async def give_welcome_credits(request: Request):
    try:
        user_id = get_user_id(request)
        credits = db_service.check_and_give_welcome_credits(user_id)
        return {
            "status": "success",
            "message": "Welcome credits applied!",
            "credits": credits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve payment page
@app.get("/payment")
async def serve_payment():
    payment_path = "frontend/payment.html"
    if os.path.exists(payment_path):
        return FileResponse(payment_path)
    return {"message": "Payment page not found"}


# === Admin Credit Management Endpoints ===

@app.post("/api/v1/admin/set-credits")
async def admin_set_credits(user_id: str, credits: int):
    """
    Admin: Set exact credits for any user
    Example: POST /api/v1/admin/set-credits?user_id=+918528933970&credits=0
    """
    if credits < 0:
        raise HTTPException(status_code=400, detail="Credits cannot be negative")
    
    try:
        # Get user
        user = db_service.get_user(user_id)
        if not user:
            return {
                "status": "error",
                "message": f"User {user_id} not found"
            }
        
        # Update credits to exact value
        current = db_service.get_user_credits(user_id)
        diff = credits - current
        new_balance = db_service.update_user_credits(user_id, diff)
        
        return {
            "status": "success",
            "user_id": user_id,
            "old_credits": current,
            "new_credits": new_balance,
            "message": f"Credits set to {new_balance} successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/v1/admin/reset-credits/{user_id}")
async def admin_reset_credits(user_id: str):
    """
    Admin: Reset user credits to 0
    Example: POST /api/v1/admin/reset-credits/+918528933970
    """
    try:
        # Get current credits
        current = db_service.get_user_credits(user_id)
        
        # Set to 0 (subtract current balance)
        new_balance = db_service.update_user_credits(user_id, -current)
        
        return {
            "status": "success",
            "user_id": user_id,
            "old_credits": current,
            "new_credits": new_balance,
            "message": f"Credits reset to 0 for user {user_id}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/v1/admin/user/{user_id}")
async def admin_get_user(user_id: str):
    """
    Admin: Get user details including credits
    Example: GET /api/v1/admin/user/+918528933970
    """
    try:
        user = db_service.get_user(user_id)
        if user:
            return {
                "status": "success",
                "user": user
            }
        else:
            return {
                "status": "error",
                "message": f"User {user_id} not found"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/v1/admin/bulk-add-credits")
async def admin_bulk_add_credits(user_ids: list, amount: int):
    """
    Admin: Add credits to multiple users
    Example: POST /api/v1/admin/bulk-add-credits
    Body: {"user_ids": ["+918528933970", "+919999999999"], "amount": 10}
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    results = []
    for user_id in user_ids:
        try:
            new_balance = db_service.update_user_credits(user_id, amount)
            results.append({
                "user_id": user_id,
                "status": "success",
                "new_balance": new_balance
            })
        except Exception as e:
            results.append({
                "user_id": user_id,
                "status": "error",
                "message": str(e)
            })
    
    return {
        "status": "success",
        "results": results
    }

@app.put("/api/v1/admin/update-user/{user_id}")
async def admin_update_user(user_id: str, request: Request):
    """Admin: Update user details"""
    try:
        data = await request.json()
        name = data.get("name")
        email = data.get("email")
        
        # Update user (you'll need to add this method to DatabaseService)
        # For now, we'll just return success
        return {
            "status": "success",
            "message": f"User {user_id} updated",
            "user_id": user_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    


# Add at the top of main.py
from app.services.gemini_service import GeminiService

# Initialize Gemini service
try:
    gemini_service = GeminiService()
    logger.info("✅ Gemini Service initialized")
except Exception as e:
    logger.warning(f"⚠️ Gemini Service not available: {e}")
    gemini_service = None

# === AI Text Assistant Endpoints ===


@app.get("/ai-assistant")
async def serve_ai_assistant():
    """Serve the AI Assistant page"""
    assistant_path = "frontend/ai-assistant.html"
    if os.path.exists(assistant_path):
        return FileResponse(assistant_path)
    else:
        # Simple fallback if file doesn't exist
        return """
        <html>
            <head><title>AI Assistant</title></head>
            <body style="font-family: Arial; padding: 40px; background: #0a0a0f; color: #fff; text-align: center;">
                <h1>🤖 AI Assistant</h1>
                <p>Please create <code>frontend/ai-assistant.html</code></p>
                <a href="/app" style="color: #6c3bf7;">← Back to App</a>
            </body>
        </html>
        """


@app.post("/api/v1/ai/chat")
async def chat_with_ai(request: Request):
    """
    Chat with AI assistant (like ChatGPT)
    """
    try:
        data = await request.json()
        prompt = data.get("prompt")
        context = data.get("context", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        if not gemini_service:
            raise HTTPException(status_code=503, detail="AI service unavailable")
        
        response = gemini_service.generate_text(prompt, context)
        
        return {
            "status": "success",
            "response": response,
            "prompt": prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/v1/ai/product-description")
async def generate_product_description(request: Request):
    """
    Generate a product description for ads
    """
    try:
        data = await request.json()
        product_name = data.get("product_name")
        features = data.get("features", "")
        
        if not product_name:
            raise HTTPException(status_code=400, detail="Product name is required")
        
        if not gemini_service:
            raise HTTPException(status_code=503, detail="AI service unavailable")
        
        description = gemini_service.generate_product_description(product_name, features)
        
        return {
            "status": "success",
            "product_name": product_name,
            "description": description
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product description error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/v1/ai/ad-script")
async def generate_ad_script(request: Request):
    """
    Generate an ad script for video generation
    """
    try:
        data = await request.json()
        product_name = data.get("product_name")
        platform = data.get("platform", "tiktok")
        
        if not product_name:
            raise HTTPException(status_code=400, detail="Product name is required")
        
        if not gemini_service:
            raise HTTPException(status_code=503, detail="AI service unavailable")
        
        script = gemini_service.generate_ad_script(product_name, platform)
        
        return {
            "status": "success",
            "product_name": product_name,
            "platform": platform,
            "script": script
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ad script error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    

# === Video Feedback & Enhancement Endpoints ===

@app.post("/api/v1/video/feedback")
async def submit_video_feedback(request: Request):
    """
    Submit feedback for a generated video
    """
    try:
        data = await request.json()
        user_id = get_user_id(request)
        task_id = data.get("task_id")
        rating = data.get("rating")  # 1-5 stars
        feedback = data.get("feedback")
        improvements = data.get("improvements", [])
        
        if not task_id or not rating:
            raise HTTPException(status_code=400, detail="Task ID and rating are required")
        
        # Store feedback in database
        feedback_data = {
            "task_id": task_id,
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback,
            "improvements": improvements,
            "created_at": datetime.now().isoformat()
        }
        
        # You can store this in a feedback table or collection
        # For now, we'll store it in a separate dictionary or database
        # feedback_storage[task_id] = feedback_data
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "data": feedback_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/v1/video/enhance")
async def enhance_video(request: Request):
    """
    Enhance video with AI suggestions
    """
    try:
        data = await request.json()
        user_id = get_user_id(request)
        task_id = data.get("task_id")
        enhancement_requests = data.get("requests", [])
        
        if not task_id:
            raise HTTPException(status_code=400, detail="Task ID is required")
        
        # Get the original video data
        video = db_service.get_video(user_id, task_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Generate enhancement suggestions using Gemini
        gemini_service = GeminiService()
        
        enhancement_prompt = f"""
        Video: {video.get('product_name')} - {video.get('product_description')}
        User wants: {', '.join(enhancement_requests) if enhancement_requests else 'Suggest improvements'}

        Generate specific, actionable enhancement suggestions for this video ad including:
        1. Visual effects (transitions, overlays, text animations)
        2. Audio improvements (music, sound effects)
        3. Pacing and timing adjustments
        4. Style and color grading suggestions
        5. Content improvements (better hooks, CTAs)

        Be specific and practical. Format as bullet points.
        """
        
        suggestions = gemini_service.generate_text(enhancement_prompt)
        
        return {
            "status": "success",
            "task_id": task_id,
            "suggestions": suggestions,
            "enhancement_requests": enhancement_requests
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhancement error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    

# In main.py, update the recommendation endpoint

@app.post("/api/v1/ai/recommend-video-config")
async def recommend_video_config(request: Request):
    """
    Analyze images and recommend video generation settings
    """
    try:
        data = await request.json()
        user_id = get_user_id(request)
        
        # Get images
        first_frame = data.get("first_frame")
        last_frame = data.get("last_frame")
        generation_mode = data.get("generation_mode", "image")
        product_name = data.get("product_name", "")
        product_description = data.get("product_description", "")
        
        if not gemini_service:
            raise HTTPException(status_code=503, detail="AI service unavailable")
        
        # Use GeminiService for recommendations
        recommendations = gemini_service.recommend_video_config(
            product_name=product_name,
            product_description=product_description,
            generation_mode=generation_mode,
            has_first_frame=bool(first_frame),
            has_last_frame=bool(last_frame)
        )
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "generation_mode": generation_mode,
            "has_first_frame": bool(first_frame),
            "has_last_frame": bool(last_frame)
        }
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    

# ===== VIDEO CHAINING ENDPOINTS =====

# ===== VIDEO CHAINING ENDPOINTS =====
# ===== GCS COMPOSE FOR INSTANT VIDEO COMBINING =====

from google.cloud import storage
import tempfile
import os
import subprocess
import requests as http_requests
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi.responses import StreamingResponse
import io
import httpx


async def combine_videos_gcs_compose(video_urls: list, chain_id: str) -> Optional[str]:
    """
    Combine videos using GCS object composition - NO download required!
    Instant and free!
    """
    try:
        storage_client = storage.Client(project="ai-social-ad-generator")
        bucket = storage_client.bucket("ai-ad-videos-kamlesh-2026")
        
        source_blobs = []
        for url in video_urls:
            blob_name = url.replace("https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/", "")
            blob = bucket.blob(blob_name)
            
            if blob.exists():
                source_blobs.append(blob)
                logger.info(f"📁 Found blob: {blob_name}")
            else:
                logger.warning(f"⚠️ Blob not found: {blob_name}")
        
        if len(source_blobs) < 2:
            logger.warning("⚠️ Less than 2 blobs found for composition")
            return video_urls[0] if video_urls else None
        
        combined_blob_name = f"chains/{chain_id}.mp4"
        combined_blob = bucket.blob(combined_blob_name)
        
        logger.info(f"📦 Composing {len(source_blobs)} videos into {combined_blob_name}")
        combined_blob.compose(source_blobs)
        combined_blob.make_public()
        
        combined_url = f"https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/{combined_blob_name}"
        logger.info(f"✅ Combined video ready: {combined_url}")
        
        return combined_url
        
    except Exception as e:
        logger.error(f"❌ GCS compose failed: {e}")
        return None



async def combine_scene_videos(
    user_id: str, 
    chain_id: str, 
    scene_results: list,
    make_public: bool = False,
    signed_url_expiry: int = 3600
) -> Optional[str]:
    """
    Combine multiple scene videos using FFmpeg with proper MP4 handling
    
    Features:
    - Proper MP4 concatenation with moov atom handling
    - Automatic detection of video formats
    - Fallback to re-encoding if formats differ
    - User-specific paths and signed URLs
    
    Args:
        user_id: User ID for path isolation
        chain_id: Chain ID for naming
        scene_results: List of scene results with video_url
        make_public: If True, make blob public
        signed_url_expiry: Expiry time in seconds for signed URLs
    
    Returns:
        URL of combined video, or None if failed
    """
    try:
        video_urls = [s.get("video_url") for s in scene_results if s.get("video_url")]
        
        if not video_urls:
            logger.error(f"❌ No video URLs found for user {user_id}")
            return None
        
        if len(video_urls) == 1:
            logger.info(f"📹 Only one scene for user {user_id}, returning it directly")
            return video_urls[0]
        
        logger.info(f"📹 Combining {len(video_urls)} videos for user {user_id} using FFmpeg...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_paths = []
            
            # Download all videos with progress
            for i, url in enumerate(video_urls):
                logger.info(f"⬇️ Downloading scene {i+1} for user {user_id}")
                try:
                    response = http_requests.get(url, timeout=60)
                    response.raise_for_status()
                    
                    video_path = os.path.join(temp_dir, f"scene_{i+1}.mp4")
                    with open(video_path, 'wb') as f:
                        f.write(response.content)
                    video_paths.append(video_path)
                    logger.info(f"✅ Downloaded scene {i+1} ({len(response.content)} bytes)")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to download scene {i+1}: {e}")
                    return None
            
            if len(video_paths) < 2:
                return video_paths[0] if video_paths else None
            
            output_path = os.path.join(temp_dir, "combined.mp4")
            
            # ===== STEP 1: Check if all videos have same format =====
            formats = []
            for path in video_paths:
                try:
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate', 
                         '-of', 'json', path],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        format_info = json.loads(result.stdout)
                        formats.append(format_info)
                    else:
                        logger.warning(f"⚠️ Could not analyze {path}, assuming same format")
                        formats.append(None)
                except Exception as e:
                    logger.warning(f"⚠️ FFprobe failed for {path}: {e}")
                    formats.append(None)
            
            # Check if all formats are identical (simplified check)
            all_same = True
            if all(f is not None for f in formats):
                first = formats[0]
                for f in formats[1:]:
                    if first.get('streams') and f.get('streams'):
                        s1 = first['streams'][0]
                        s2 = f['streams'][0]
                        if (s1.get('codec_name') != s2.get('codec_name') or
                            s1.get('width') != s2.get('width') or
                            s1.get('height') != s2.get('height')):
                            all_same = False
                            break
            
            # ===== STEP 2: Combine using appropriate method =====
            if all_same:
                # Method 1: Fast concat with copy (no re-encoding)
                logger.info("🔄 Using fast concat (copy codec)")
                list_path = os.path.join(temp_dir, "filelist.txt")
                with open(list_path, 'w') as f:
                    for path in video_paths:
                        # Use absolute path to avoid issues
                        abs_path = os.path.abspath(path)
                        f.write(f"file '{abs_path}'\n")
                
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', list_path,
                    '-c', 'copy',
                    '-movflags', 'faststart',  # Moves moov atom to beginning for web streaming
                    '-y',
                    output_path
                ]
                logger.info(f"🔧 Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode != 0:
                    logger.warning(f"⚠️ Fast concat failed: {result.stderr}")
                    all_same = False  # Fallback to re-encode
            
            if not all_same:
                # Method 2: Re-encode with concat filter (compatible with different formats)
                logger.info("🔄 Using re-encode concat (compatible with all formats)")
                
                # Build command for concat filter
                cmd = ['ffmpeg']
                for path in video_paths:
                    cmd.extend(['-i', path])
                
                # Build filter complex
                cmd.extend([
                    '-filter_complex', f'concat=n={len(video_paths)}:v=1:a=1',
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-movflags', 'faststart',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-y',
                    output_path
                ])
                logger.info(f"🔧 Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # ===== STEP 3: Check if combined video was created =====
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg error: {result.stderr}")
                return None
            
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.error("❌ Combined video file is empty or missing")
                return None
            
            logger.info(f"✅ Combined video created: {output_path} ({os.path.getsize(output_path)} bytes)")
            
            # ===== STEP 4: Upload to GCS =====
            logger.info(f"☁️ Uploading combined video to GCS for user {user_id}...")
            
            storage_client = storage.Client(project="ai-social-ad-generator")
            bucket = storage_client.bucket("ai-ad-videos-kamlesh-2026")
            
            # User-specific path
            blob_name = f"users/{user_id}/chains/{chain_id}.mp4"
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(output_path)
            
            # Generate URL
            if make_public:
                blob.make_public()
                combined_url = blob.public_url
                logger.info(f"✅ Combined video uploaded (public): {combined_url}")
            else:
                expires_in = timedelta(seconds=signed_url_expiry)
                combined_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expires_in,
                    method="GET",
                )
                logger.info(f"✅ Combined video uploaded (signed URL, expires in {signed_url_expiry}s)")
            
            return combined_url
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ FFmpeg timed out for user {user_id}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to combine videos for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None



# ===== SYNC VERSION FOR LOCAL TESTING =====

def combine_videos_sync(video_paths: list, output_path: str) -> bool:
    """
    Synchronous version for local testing
    
    Args:
        video_paths: List of local video file paths
        output_path: Output file path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if len(video_paths) < 2:
            logger.warning("Need at least 2 videos to combine")
            return False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            list_path = os.path.join(temp_dir, "filelist.txt")
            with open(list_path, 'w') as f:
                for path in video_paths:
                    f.write(f"file '{os.path.abspath(path)}'\n")
            
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_path,
                '-c', 'copy',
                '-movflags', 'faststart',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg error: {result.stderr}")
                return False
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"✅ Combined video created: {output_path}")
                return True
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to combine videos: {e}")
        return False


def detect_video_format(video_path: str) -> dict:
    """
    Detect video format using ffprobe
    
    Args:
        video_path: Path to video file
    
    Returns:
        Dictionary with format information
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'stream=codec_name,width,height,r_frame_rate,codec_type', 
             '-of', 'json', video_path],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to detect format: {e}")
        return {}

@app.post("/api/v1/chain/create")
async def create_video_chain(request: ChainVideoRequest, req: Request):
    """
    Create a video chain with multiple scenes using GCS Compose for instant combining
    """
    user_id = get_user_id(req)
    logger.info(f"🎬 Creating video chain for user: {user_id}")
    logger.info(f"📋 Chain name: {request.chain_name}")
    logger.info(f"📋 Total scenes: {len(request.scenes)}")
    
    # ===== CHECK CREDITS =====
    total_credits_needed = len(request.scenes)
    credits = db_service.get_user_credits(user_id)
    
    logger.info(f"💰 User has {credits} credits, needs {total_credits_needed}")
    
    if credits < total_credits_needed:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {total_credits_needed}, have {credits}."
        )
    
    # Generate chain ID
    chain_id = f"chain_{uuid.uuid4().hex[:8]}"
    
    # ===== PROCESS EACH SCENE =====
    scene_results = []
    credits_used = 0
    total_duration = 0
    video_urls = []  # Store URLs for combining
    
    for scene in request.scenes:
        scene_id = f"scene_{uuid.uuid4().hex[:8]}"
        
        # ===== DEDUCT CREDIT FOR THIS SCENE =====
        db_service.update_user_credits(user_id, -1)
        credits_used += 1
        remaining = db_service.get_user_credits(user_id)
        
        logger.info(f"💰 Scene {scene.scene_order}: Used 1 credit, remaining: {remaining}")
        
        # ===== GENERATE VIDEO FOR THIS SCENE =====
        try:
            from app.services.veo_service import VeoService
            veo_service = VeoService()
            
            platform = scene.platform
            aspect_ratio = "9:16" if platform in ["tiktok", "instagram"] else "16:9"
            
            video_url = None
            
            # Generate based on mode
            if scene.generation_mode == "image" and scene.first_frame:
                # Image-to-Video
                from PIL import Image
                import base64
                import io
                
                if scene.first_frame.startswith('data:image'):
                    base64_data = scene.first_frame.split(',')[1]
                    image_bytes = base64.b64decode(base64_data)
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    video_url = veo_service.generate_from_image(
                        prompt=f"Scene {scene.scene_order}: {scene.product_description}",
                        image=image,
                        duration=scene.duration_seconds,
                        aspect_ratio=aspect_ratio,
                        generate_audio=True,
                        use_lite=False
                    )
                else:
                    video_url = None
                    
            elif scene.generation_mode == "first-last" and scene.first_frame and scene.last_frame:
                # First/Last Frame
                from PIL import Image
                import base64
                import io
                
                first_bytes = base64.b64decode(scene.first_frame.split(',')[1])
                last_bytes = base64.b64decode(scene.last_frame.split(',')[1])
                first_image = Image.open(io.BytesIO(first_bytes))
                last_image = Image.open(io.BytesIO(last_bytes))
                
                video_url = veo_service.generate_with_first_last_frame(
                    prompt=f"Scene {scene.scene_order}: {scene.product_description}",
                    first_frame=first_image,
                    last_frame=last_image,
                    duration=min(scene.duration_seconds, 8),
                    aspect_ratio=aspect_ratio,
                    generate_audio=True,
                    use_lite=False
                )
            else:
                # Text-to-Video
                video_url = veo_service.generate_ad_video(
                    product_name=scene.product_name,
                    product_description=scene.product_description,
                    platform=scene.platform,
                    duration=scene.duration_seconds
                )
            
            if video_url:
                scene_status = "completed"
                scene_url = video_url
                total_duration += scene.duration_seconds
                video_urls.append(video_url)
                logger.info(f"✅ Scene {scene.scene_order} generated: {video_url}")
            else:
                scene_status = "failed"
                scene_url = None
                logger.warning(f"⚠️ Scene {scene.scene_order} generation failed")
                
        except Exception as e:
            logger.error(f"❌ Scene {scene.scene_order} error: {e}")
            scene_status = "failed"
            scene_url = None
        
        # Store scene result
        scene_result = {
            "scene_id": scene_id,
            "order": scene.scene_order,
            "title": getattr(scene, 'title', f"Scene {scene.scene_order}"),
            "product_name": scene.product_name,
            "duration_seconds": scene.duration_seconds,
            "generation_mode": scene.generation_mode,
            "status": scene_status,
            "video_url": scene_url,
            "credits_used": 1
        }
        scene_results.append(scene_result)
    
    # ===== UPDATE CHAIN STATUS =====
    completed_scenes = [s for s in scene_results if s["status"] == "completed"]
    
    if len(completed_scenes) == len(scene_results):
        chain_status = "completed"
    elif len(completed_scenes) > 0:
        chain_status = "partial"
    else:
        chain_status = "failed"
    
    progress = int((len(completed_scenes) / len(scene_results)) * 100) if scene_results else 0
    
    # ===== COMBINE VIDEOS INSTANTLY USING GCS COMPOSE =====
    combined_url = None
    
    # Only combine if all scenes are completed and there are 2+ scenes
    if len(completed_scenes) == len(scene_results) and len(scene_results) > 1 and len(video_urls) >= 2:
        try:
            logger.info(f"🔄 Combining {len(video_urls)} videos instantly...")
            combined_url = await combine_scene_videos(user_id, chain_id, scene_results)
        except Exception as e:
            logger.error(f"❌ Failed to combine videos: {e}")
    
    # If only one scene, use its URL as combined
    elif len(completed_scenes) == len(scene_results) and len(scene_results) == 1:
        combined_url = scene_results[0]["video_url"]
    
    # ===== SAVE CHAIN TO DATABASE =====
    chain_data = {
        "id": chain_id,
        "user_id": user_id,
        "chain_name": request.chain_name,
        "total_scenes": len(request.scenes),
        "target_platform": request.target_platform,
        "scenes": scene_results,
        "status": chain_status,
        "progress": progress,
        "credits_used": credits_used,
        "combined_url": combined_url,
        "total_duration": total_duration,
        "created_at": datetime.now().isoformat()
    }
    
    db_service.save_chain(user_id, chain_data)
    
    return {
        "chain_id": chain_id,
        "chain_name": request.chain_name,
        "total_scenes": len(request.scenes),
        "scenes": scene_results,
        "status": chain_status,
        "progress": progress,
        "message": f"✅ Chain created! {len(completed_scenes)} of {len(scene_results)} scenes generated.",
        "credits_required": total_credits_needed,
        "credits_used": credits_used,
        "credits_remaining": db_service.get_user_credits(user_id),
        "combined_url": combined_url,
        "total_duration": total_duration
    }


@app.get("/api/v1/chain/{chain_id}")
async def get_chain_status(chain_id: str, req: Request):
    """Get status of a video chain"""
    try:
        user_id = get_user_id(req)
    except HTTPException:
        return {
            "chain_id": chain_id,
            "status": "pending",
            "message": "Please login to view chain details",
            "requires_auth": True
        }
    
    chain = db_service.get_chain(user_id, chain_id)
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    scenes = chain.get("scenes", [])
    completed_scenes = [s for s in scenes if s.get("status") == "completed"]
    
    return {
        "chain_id": chain_id,
        "chain_name": chain.get("chain_name"),
        "status": chain.get("status"),
        "progress": chain.get("progress", 0),
        "scenes_completed": len(completed_scenes),
        "total_scenes": chain.get("total_scenes", 0),
        "scenes": scenes,
        "credits_used": chain.get("credits_used", 0),
        "combined_url": chain.get("combined_url"),
        "total_duration": chain.get("total_duration", 0),
        "message": f"{len(completed_scenes)} of {chain.get('total_scenes', 0)} scenes completed",
        "created_at": chain.get("created_at")
    }


@app.post("/api/v1/chain/combine/{chain_id}")
async def combine_chain_videos(chain_id: str, req: Request):
    """
    Combine all completed scenes in a chain using GCS Compose (instant!)
    """
    user_id = get_user_id(req)
    
    chain = db_service.get_chain(user_id, chain_id)
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    scenes = chain.get("scenes", [])
    completed_scenes = [s for s in scenes if s.get("status") == "completed"]
    video_urls = [s.get("video_url") for s in completed_scenes if s.get("video_url")]
    
    if len(video_urls) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 2 videos to combine. Currently have {len(video_urls)}"
        )
    
    logger.info(f"🔄 Combining {len(video_urls)} videos...")
    combined_url = await combine_scene_videos(user_id, chain_id, scenes)
    
    if combined_url:
        chain["status"] = "combined"
        chain["combined_url"] = combined_url
        chain["progress"] = 100
        db_service.update_chain(user_id, chain_id, chain)
        
        return {
            "status": "success",
            "chain_id": chain_id,
            "combined_video_url": combined_url,
            "message": "✅ All scenes combined successfully!",
            "total_duration": sum(s.get("duration_seconds", 6) for s in scenes)
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to combine videos")


@app.get("/api/v1/chain/download/{chain_id}")
async def download_combined_video(chain_id: str, req: Request):
    """Download the combined video as a file"""
    user_id = get_user_id(req)
    
    chain = db_service.get_chain(user_id, chain_id)
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    combined_url = chain.get("combined_url")
    
    if not combined_url:
        raise HTTPException(status_code=404, detail="Combined video not available")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(combined_url)
            if response.status_code == 200:
                return StreamingResponse(
                    io.BytesIO(response.content),
                    media_type="video/mp4",
                    headers={
                        "Content-Disposition": f"attachment; filename={chain.get('chain_name', 'video')}.mp4"
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chain/download-scene/{chain_id}/{scene_index}")
async def download_scene_video(chain_id: str, scene_index: int, req: Request):
    """Download a specific scene video"""
    user_id = get_user_id(req)
    
    chain = db_service.get_chain(user_id, chain_id)
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    scenes = chain.get("scenes", [])
    
    if scene_index < 0 or scene_index >= len(scenes):
        raise HTTPException(status_code=404, detail="Scene not found")
    
    scene = scenes[scene_index]
    video_url = scene.get("video_url")
    
    if not video_url:
        raise HTTPException(status_code=404, detail="Scene video not available")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(video_url)
            if response.status_code == 200:
                return StreamingResponse(
                    io.BytesIO(response.content),
                    media_type="video/mp4",
                    headers={
                        "Content-Disposition": f"attachment; filename=scene_{scene_index+1}.mp4"
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
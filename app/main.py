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

# === Models ===

# Add this helper function at the top of main.py
# In app/main.py, update the get_user_id function:

def get_user_id(request: Request) -> str:
    """
    Extract user ID from request headers.
    For admin endpoints, use a default admin user if header is missing.
    """
    user_id = request.headers.get("X-User-ID")
    
    # For admin endpoints, allow fallback to admin user
    if not user_id:
        path = request.url.path
        # Admin endpoints that should show all data
        admin_endpoints = ["/api/v1/users", "/api/v1/tasks", "/api/v1/analytics"]
        if any(path.startswith(endpoint) for endpoint in admin_endpoints):
            # Use a default admin user that has access to all data
            user_id = "+919999999999"
            logger.info(f"👤 Admin endpoint: using admin user {user_id}")
        else:
            logger.error("❌ No X-User-ID found in request headers")
            raise HTTPException(
                status_code=401,
                detail="User ID not provided. Please include X-User-ID header."
            )
    
    logger.info(f"👤 User ID from header: {user_id}")
    return user_id




class GenerateVideoRequest(BaseModel):
    platform: str = Field(..., description="tiktok, instagram, or youtube")
    product_name: str = Field(..., description="Name of the product")
    product_description: str = Field(..., description="Description of the product")
    duration_seconds: int = Field(6, ge=4, le=8, description="Video duration (4, 6, or 8 seconds)")
    template_id: Optional[str] = Field(None, description="Template ID to use")
    enhance_prompt: bool = Field(True, description="Enhance prompt with AI")
    generate_audio: bool = Field(True, description="Generate audio for video")
    
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

# === Sample Videos Fallback ===
SAMPLE_VIDEOS = [
    "https://storage.googleapis.com/ai-ad-videos-kamlesh-2026/demo/sample.mp4",
    "https://www.w3schools.com/html/mov_bbb.mp4",
]

# === Helper Functions ===
# === REPLACE the get_user_id function with this ===
def get_user_id(request: Request) -> str:
    """
    Extract user ID from request headers.
    Returns the user ID or raises an exception if not found.
    """
    # Try to get from header
    user_id = request.headers.get("X-User-ID")
    
    # Also try to get from Authorization header (if using JWT)
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # You could decode JWT here to get user_id
            pass
    
    # Log the request headers for debugging
    logger.info(f"📋 Request headers: {dict(request.headers)}")
    
    # If still no user_id, raise an error
    if not user_id:
        logger.error("❌ No X-User-ID found in request headers")
        raise HTTPException(
            status_code=401,
            detail="User ID not provided. Please include X-User-ID header."
        )
    
    logger.info(f"👤 User ID from header: {user_id}")
    return user_id

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
            "Analytics"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check with database status"""
    db_status = "connected"
    try:
        # Test database connection
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

# === Video Generation Endpoints ===


# Update the generate endpoint
@app.post("/api/v1/generate", response_model=GenerateVideoResponse)
async def generate_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """Generate a video using REAL AI"""
    user_id = get_user_id(req)
    logger.info(f"🎬 Generation requested for user: {user_id}")
    
    # Check credits
    credits = db_service.get_user_credits(user_id)
    logger.info(f"💰 User {user_id} has {credits} credits")
    
    if credits < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    logger.info(f"📋 Created task ID: {task_id}")
    
    # Deduct credits
    db_service.update_user_credits(user_id, -1)
    logger.info(f"💰 Deducted 1 credit from {user_id}")
    
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
        "progress": 0
    }
    db_service.save_video(user_id, video_data)
    logger.info(f"💾 Saved video record to database")
    
    # Start background processing
    logger.info(f"🚀 Adding background task for {task_id}")
    background_tasks.add_task(
        process_video_generation_db,
        task_id,
        request.dict(),
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





# Update the status endpoint
@app.get("/api/v1/status/{task_id}")
async def get_generation_status(task_id: str, req: Request):
    """Check the status of a video generation task with detailed progress"""
    user_id = get_user_id(req)
    
    # Get video from database
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
    
    # Get the progress
    progress = video.get("progress", 0)
    status = video.get("status", "unknown")
    
    # Add a meaningful message based on progress
    messages = {
        0: "⏳ Queued...",
        10: "⏳ Starting generation...",
        20: "🤖 Initializing AI model...",
        30: "🎬 Generating video...",
        40: "🎬 Creating scenes...",
        50: "🎬 Adding effects...",
        60: "🎬 Finalizing content...",
        70: "🎬 Rendering video...",
        80: "📤 Preparing for upload...",
        90: "☁️ Uploading to cloud...",
        100: "✅ Complete!",
    }
    
    # Find the closest message
    message = "⏳ Processing..."
    for p in sorted(messages.keys(), reverse=True):
        if progress >= p:
            message = messages[p]
            break
    
    # If status is completed, update message
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
    """
    ⚡ Generate and auto-complete instantly (for testing)
    Uses sample videos, not real AI
    """
    user_id = get_user_id(req)
    
    if db_service.get_user_credits(user_id) < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    video_id = f"auto_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    db_service.update_user_credits(user_id, -1)
    
    video_url = random.choice(SAMPLE_VIDEOS)
    
    # Save to PostgreSQL
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


# Update the cancel endpoint
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
    """
    Generate multiple videos at once (for bulk discounts)
    """
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
# Update the credits endpoint
@app.get("/api/v1/credits/balance")
async def get_credit_balance(req: Request):
    """Get user's credit balance"""
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



# Update the add credits endpoint
@app.post("/api/v1/credits/add")
async def add_credits(amount: int = 10, req: Request = None):
    """Add credits for testing"""
    user_id = get_user_id(req) if req else "demo_user"
    
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

# === Error Handlers ===

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)}
    )



# === Admin Endpoints ===

@app.get("/api/v1/users")
async def get_all_users():
    """Get all users (Admin only)"""
    users = db_service.get_all_users()
    return {
        "total": len(users),
        "users": users
    }

@app.post("/api/v1/admin/add-credits")
async def admin_add_credits(user_id: str, amount: int):
    """Admin: Add credits to any user"""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    new_balance = db_service.update_user_credits(user_id, amount)
    return {
        "status": "success",
        "user_id": user_id,
        "credits_added": amount,
        "new_balance": new_balance
    }

@app.delete("/api/v1/admin/delete-user/{user_id}")
async def admin_delete_user(user_id: str):
    """Admin: Delete a user and all their data"""
    # This would need to be implemented in the database service
    return {"status": "success", "message": f"User {user_id} deleted"}



@app.get("/admin")
async def serve_admin():
    """Serve the admin panel"""
    admin_path = "frontend/admin.html"
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"message": "Admin panel not found"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
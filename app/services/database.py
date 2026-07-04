"""
PostgreSQL Database Models using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)
load_dotenv()

Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:studio45@127.0.0.1:5433/ai_ad_generator")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True to see SQL logs
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# === User Model ===
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)  # phone number as ID
    name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    credits = Column(Integer, default=10)
    total_videos = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "credits": self.credits,
            "total_videos": self.total_videos,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# === Video Model ===
class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_url = Column(String(500), nullable=False, default="")
    platform = Column(String(20), default="tiktok")
    product_name = Column(String(255), nullable=False)
    product_description = Column(Text, nullable=True)
    duration_seconds = Column(Integer, default=6)
    status = Column(String(20), default="pending")
    credits_used = Column(Integer, default=1)
    file_size = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    task_id = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="videos")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "video_url": self.video_url,
            "platform": self.platform,
            "product_name": self.product_name,
            "product_description": self.product_description,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "credits_used": self.credits_used,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# === Purchase Model ===
class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    credits_purchased = Column(Integer, nullable=False)
    payment_method = Column(String(50), default="stripe")
    payment_id = Column(String(255), nullable=True)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "credits_purchased": self.credits_purchased,
            "payment_method": self.payment_method,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# === Create Tables ===
def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

def get_db():
    """Get database session - for FastAPI dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Database Service ===
class DatabaseService:
    """Service class for database operations"""
    
    def __init__(self):
        self.SessionLocal = SessionLocal
    
    def get_session(self):
        return self.SessionLocal()
    
    # === User CRUD ===
    def create_user(self, user_id: str, user_data: dict) -> dict:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.name = user_data.get("name", user.name)
                user.email = user_data.get("email", user.email)
            else:
                user = User(
                    id=user_id,
                    name=user_data.get("name", user_id),
                    email=user_data.get("email", ""),
                    credits=user_data.get("credits", 10),
                    total_videos=0  # ✅ Set default
                )
                session.add(user)
            session.commit()
            session.refresh(user)
            return user.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user(self, user_id: str) -> dict:
        """Get user by ID"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user.to_dict() if user else None
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> dict:
        """Get user by email"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            return user.to_dict() if user else None
        finally:
            session.close()
    
    def get_all_users(self) -> list:
        """Get all users (for admin)"""
        session = self.get_session()
        try:
            users = session.query(User).all()
            return [user.to_dict() for user in users]
        finally:
            session.close()
    
    def update_user_credits(self, user_id: str, amount: int) -> int:
        """
        Update user credits (can be negative)
        Handles NULL values gracefully
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # ✅ Handle NULL values
                if user.credits is None:
                    user.credits = 0
                    logger.info(f"💰 Initialized NULL credits to 0 for user {user_id}")
                
                user.credits += amount
                session.commit()
                session.refresh(user)
                logger.info(f"💰 User {user_id} credits updated: {user.credits}")
                return user.credits
            else:
                logger.error(f"❌ User {user_id} not found")
                return 0
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to update credits: {e}")
            raise e
        finally:
            session.close()
    
    def get_user_credits(self, user_id: str) -> int:
        """Get user credits"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user.credits if user else 0
        finally:
            session.close()
    
    # === Video CRUD ===
    def save_video(self, user_id: str, video_data: dict) -> dict:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # ✅ Handle NULL total_videos
            if user.total_videos is None:
                user.total_videos = 0
            
            video_id = video_data.get("id", f"vid_{int(datetime.now().timestamp())}")
            video = session.query(Video).filter(Video.id == video_id).first()
            
            if video:
                video.video_url = video_data.get("video_url", video.video_url)
                video.platform = video_data.get("platform", video.platform)
                video.product_name = video_data.get("product_name", video.product_name)
                video.product_description = video_data.get("product_description", video.product_description)
                video.duration_seconds = video_data.get("duration_seconds", video.duration_seconds)
                video.status = video_data.get("status", video.status)
                video.credits_used = video_data.get("credits_used", video.credits_used)
                video.error_message = video_data.get("error_message", None)
                video.progress = video_data.get("progress", 0)
            else:
                video = Video(
                    id=video_id,
                    user_id=user_id,
                    video_url=video_data.get("video_url", ""),
                    platform=video_data.get("platform", "tiktok"),
                    product_name=video_data.get("product_name", ""),
                    product_description=video_data.get("product_description", ""),
                    duration_seconds=video_data.get("duration_seconds", 6),
                    status=video_data.get("status", "pending"),
                    credits_used=video_data.get("credits_used", 1),
                    task_id=video_data.get("task_id", None),
                    error_message=video_data.get("error_message", None),
                    progress=video_data.get("progress", 0)
                )
                session.add(video)
                user.total_videos += 1
            
            session.commit()
            session.refresh(video)
            return video.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_videos(self, user_id: str, limit: int = 50, offset: int = 0) -> list:
        """Get user's videos with pagination"""
        session = self.get_session()
        try:
            videos = session.query(Video).filter(
                Video.user_id == user_id
            ).order_by(
                Video.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return [video.to_dict() for video in videos]
        finally:
            session.close()
    
    def get_user_video_count(self, user_id: str) -> int:
        """Get total video count for a user"""
        session = self.get_session()
        try:
            count = session.query(Video).filter(Video.user_id == user_id).count()
            return count
        finally:
            session.close()
    
    def get_video(self, user_id: str, video_id: str) -> dict:
        """Get a specific video"""
        session = self.get_session()
        try:
            video = session.query(Video).filter(
                Video.id == video_id,
                Video.user_id == user_id
            ).first()
            return video.to_dict() if video else None
        finally:
            session.close()
    
    # In app/models/database.py, update the method:

    def update_video_status(self, user_id: str, video_id: str, status: str, 
                        video_url: str = None, error: str = None, 
                        progress: int = None) -> bool:
        """
        Update video status
        
        Args:
            user_id: User ID
            video_id: Video ID
            status: New status (pending, processing, completed, failed, cancelled)
            video_url: Optional video URL (for completed)
            error: Optional error message (for failed)
            progress: Optional progress percentage (0-100)
        """
        session = self.get_session()
        try:
            video = session.query(Video).filter(
                Video.id == video_id,
                Video.user_id == user_id
            ).first()
            if video:
                video.status = status
                video.updated_at = datetime.now()
                if video_url:
                    video.video_url = video_url
                if error:
                    video.error_message = error
                if progress is not None:
                    video.progress = progress
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_video_progress(self, user_id: str, video_id: str, progress: int) -> bool:
        """Update video generation progress"""
        return self.update_video_status(user_id, video_id, "processing", progress=progress)
    
    def delete_video(self, user_id: str, video_id: str) -> bool:
        """Delete a video"""
        session = self.get_session()
        try:
            video = session.query(Video).filter(
                Video.id == video_id,
                Video.user_id == user_id
            ).first()
            if video:
                session.delete(video)
                # Decrement user's total videos
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.total_videos = max(0, user.total_videos - 1)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # === Purchase CRUD ===
    def add_purchase(self, user_id: str, purchase_data: dict) -> dict:
        """Add a purchase record"""
        session = self.get_session()
        try:
            purchase = Purchase(
                id=purchase_data.get("id", f"pur_{int(datetime.now().timestamp())}"),
                user_id=user_id,
                amount=purchase_data.get("amount", 0),
                credits_purchased=purchase_data.get("credits_purchased", 0),
                payment_method=purchase_data.get("payment_method", "stripe"),
                payment_id=purchase_data.get("payment_id", ""),
                status=purchase_data.get("status", "completed")
            )
            session.add(purchase)
            
            # Update user credits
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.credits += purchase.credits_purchased
            
            session.commit()
            session.refresh(purchase)
            return purchase.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_purchases(self, user_id: str, limit: int = 50) -> list:
        """Get user's purchase history"""
        session = self.get_session()
        try:
            purchases = session.query(Purchase).filter(
                Purchase.user_id == user_id
            ).order_by(
                Purchase.created_at.desc()
            ).limit(limit).all()
            
            return [purchase.to_dict() for purchase in purchases]
        finally:
            session.close()

# Create singleton instance
db_service = DatabaseService()
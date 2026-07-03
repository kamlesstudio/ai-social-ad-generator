"""
Test PostgreSQL Database Operations
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import db_service

def test_database():
    print("🧪 Testing PostgreSQL Database")
    print("=" * 50)
    
    # Test user creation
    print("\n📝 Creating test user...")
    user = db_service.create_user("+919999999999", {
        "name": "Test User",
        "email": "test@example.com",
        "credits": 100
    })
    print(f"✅ User created: {user}")
    
    # Test credit update
    print("\n💰 Updating credits...")
    credits = db_service.update_user_credits("+919999999999", 10)
    print(f"✅ New credit balance: {credits}")
    
    # Test video save
    print("\n🎬 Saving test video...")
    video = db_service.save_video("+919999999999", {
        "video_url": "https://example.com/test.mp4",
        "platform": "tiktok",
        "product_name": "Test Product",
        "product_description": "Test description",
        "duration_seconds": 6
    })
    print(f"✅ Video saved: {video}")
    
    # Test get user videos
    print("\n📹 Getting user videos...")
    videos = db_service.get_user_videos("+919999999999")
    print(f"✅ Found {len(videos)} videos")
    for v in videos:
        print(f"   - {v['product_name']} ({v['status']})")
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    test_database()
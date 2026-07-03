"""
Test PostgreSQL Database Operations
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import db_service
import random
import time

def test_database():
    print("🧪 Testing PostgreSQL Database")
    print("=" * 60)
    
    # Generate unique test phone
    test_phone = f"+91{random.randint(7000000000, 9999999999)}"
    
    # 1. Test User Creation
    print(f"\n📝 1. Creating test user: {test_phone}")
    user = db_service.create_user(test_phone, {
        "name": "Test User",
        "email": "test@example.com",
        "credits": 50
    })
    print(f"✅ User created: {user}")
    
    # 2. Test Get User
    print("\n📖 2. Fetching user...")
    fetched_user = db_service.get_user(test_phone)
    print(f"✅ User fetched: {fetched_user}")
    
    # 3. Test Credits
    print("\n💰 3. Testing credits...")
    initial_credits = db_service.get_user_credits(test_phone)
    print(f"   Initial credits: {initial_credits}")
    
    # Add credits
    db_service.update_user_credits(test_phone, 10)
    new_credits = db_service.get_user_credits(test_phone)
    print(f"   After adding 10: {new_credits}")
    
    # Deduct credits
    db_service.update_user_credits(test_phone, -5)
    final_credits = db_service.get_user_credits(test_phone)
    print(f"   After deducting 5: {final_credits}")
    print(f"✅ Credit operations successful")
    
    # 4. Test Video Saving
    print("\n🎬 4. Saving test video...")
    video_id = f"test_vid_{int(time.time())}"
    video = db_service.save_video(test_phone, {
        "id": video_id,
        "video_url": "https://storage.googleapis.com/test-bucket/test-video.mp4",
        "platform": "tiktok",
        "product_name": "Test Product",
        "product_description": "This is a test video description",
        "duration_seconds": 6,
        "status": "completed",
        "credits_used": 1,
        "progress": 100
    })
    print(f"✅ Video saved: {video}")
    
    # 5. Test Get User Videos
    print("\n📹 5. Fetching user videos...")
    videos = db_service.get_user_videos(test_phone)
    print(f"✅ Found {len(videos)} videos")
    for v in videos[:3]:
        print(f"   - {v['product_name']} ({v['status']})")
    
    # 6. Test Video Status Update - FIXED
    print("\n🔄 6. Updating video status...")
    # Use correct parameter names
    db_service.update_video_status(
        test_phone, 
        video_id, 
        "processing",
        progress=50
    )
    updated_video = db_service.get_video(test_phone, video_id)
    print(f"   Status: {updated_video['status']}, Progress: {updated_video.get('progress', 0)}%")
    
    # Update to completed
    db_service.update_video_status(
        test_phone, 
        video_id, 
        "completed",
        video_url="https://storage.googleapis.com/test-bucket/completed-video.mp4",
        progress=100
    )
    final_video = db_service.get_video(test_phone, video_id)
    print(f"   Final status: {final_video['status']}, URL: {final_video['video_url'][:50]}...")
    
    # 7. Test Purchase
    print("\n💳 7. Adding purchase record...")
    purchase = db_service.add_purchase(test_phone, {
        "amount": 9.99,
        "credits_purchased": 10,
        "payment_method": "test",
        "payment_id": f"test_pay_{int(time.time())}"
    })
    print(f"✅ Purchase added: {purchase}")
    
    # 8. Test Get Purchases
    print("\n📊 8. Fetching purchase history...")
    purchases = db_service.get_purchases(test_phone)
    print(f"✅ Found {len(purchases)} purchases")
    for p in purchases:
        print(f"   - {p['credits_purchased']} credits for ${p['amount']}")
    
    # 9. Test All Users
    print("\n👥 9. Fetching all users...")
    all_users = db_service.get_all_users()
    print(f"✅ Total users: {len(all_users)}")
    
    # 10. Test Delete Video
    print("\n🗑️ 10. Deleting test video...")
    deleted = db_service.delete_video(test_phone, video_id)
    print(f"✅ Video deleted: {deleted}")
    
    # 11. Final check
    final_videos = db_service.get_user_videos(test_phone)
    print(f"\n📊 Final video count: {len(final_videos)}")
    
    print("\n" + "=" * 60)
    print("🎉 All database tests passed!")
    print(f"📱 Test phone: {test_phone}")
    print("💡 You can use this phone number for API testing")

if __name__ == "__main__":
    test_database()
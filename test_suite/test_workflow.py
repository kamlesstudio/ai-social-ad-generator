"""
Complete Workflow Test - Database + API + GCP
"""

import sys
import os
import time
import json
import requests
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import db_service
from app.services.veo_service import VeoService

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

TEST_PHONE = f"+91{random.randint(7000000000, 9999999999)}"

def test_full_workflow():
    print("\n" + "=" * 70)
    print("🚀 AI Ad Generator - Complete Workflow Test")
    print("=" * 70)
    
    # Step 1: Create User
    print(f"\n📝 Step 1: Creating test user: {TEST_PHONE}")
    user = db_service.create_user(TEST_PHONE, {
        "name": "Workflow Test User",
        "email": "workflow@test.com",
        "credits": 100
    })
    print(f"✅ User created with {user['credits']} credits")
    
    # Step 2: Test Veo Service
    print("\n🎬 Step 2: Testing Veo 3 Service")
    try:
        veo = VeoService()
        print("✅ Veo Service initialized")
        
        # Test with a short prompt
        test_prompt = "A simple product showcase video"
        print(f"   Testing with: '{test_prompt}'")
        # Uncomment when ready
        # video_url = veo.generate_video(test_prompt, duration=4)
        # if video_url:
        #     print(f"✅ Video generated: {video_url[:50]}...")
    except Exception as e:
        print(f"⚠️ Veo Service test: {e}")
    
    # Step 3: API - Send OTP
    print("\n📱 Step 3: API - Send OTP")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/send-otp",
        json={"phone": TEST_PHONE}
    )
    if response.status_code == 200:
        print("✅ OTP sent (check console for OTP)")
    else:
        print(f"❌ OTP failed: {response.text}")
        return
    
    # Step 4: API - Generate Video
    print("\n🎬 Step 4: API - Generate Video")
    
    payload = {
        "platform": random.choice(["tiktok", "instagram", "youtube"]),
        "product_name": "Smart Fitness Tracker Pro",
        "product_description": "Advanced fitness tracker with AI coaching, heart rate monitoring, GPS, and 7-day battery life. Waterproof and stylish design.",
        "duration_seconds": 6
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": TEST_PHONE
    }
    
    response = requests.post(
        f"{API_URL}/generate",
        json=payload,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Generation failed: {response.text}")
        return
    
    data = response.json()
    task_id = data.get('task_id')
    credits_remaining = data.get('credits_remaining')
    print(f"✅ Video generation started!")
    print(f"   Task ID: {task_id}")
    print(f"   Credits remaining: {credits_remaining}")
    
    # Step 5: Poll for Status
    print("\n⏳ Step 5: Polling for status...")
    
    for i in range(20):  # Try 20 times
        response = requests.get(
            f"{API_URL}/status/{task_id}",
            headers={"X-User-ID": TEST_PHONE}
        )
        
        if response.status_code == 200:
            status_data = response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            print(f"   [{i+1}] Status: {status}, Progress: {progress}%")
            
            if status == 'completed':
                video_url = status_data.get('video_url')
                print(f"\n🎉 VIDEO READY!")
                print(f"   📹 URL: {video_url}")
                break
            elif status == 'failed':
                print(f"\n❌ Generation failed: {status_data.get('error_message')}")
                break
        
        time.sleep(5)
    else:
        print("\n⏱️ Timeout - Generation took too long")
    
    # Step 6: Check Database
    print("\n📊 Step 6: Checking database records")
    
    # Check user
    user = db_service.get_user(TEST_PHONE)
    print(f"   User: {user['name']}")
    print(f"   Credits: {user['credits']}")
    print(f"   Total videos: {user['total_videos']}")
    
    # Check videos
    videos = db_service.get_user_videos(TEST_PHONE)
    print(f"   Videos in DB: {len(videos)}")
    
    for v in videos:
        print(f"   - {v['product_name']} ({v['status']})")
        if v.get('video_url'):
            print(f"     URL: {v['video_url'][:60]}...")
    
    # Step 7: Check Credits API
    print("\n💰 Step 7: Checking credits via API")
    response = requests.get(
        f"{API_URL}/credits/balance",
        headers={"X-User-ID": TEST_PHONE}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   Balance: {data.get('balance')} credits")
    
    # Step 8: Check User Videos API
    print("\n📹 Step 8: Fetching user videos via API")
    response = requests.get(
        f"{API_URL}/user/videos?limit=10",
        headers={"X-User-ID": TEST_PHONE}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   Total videos: {data.get('total')}")
        for v in data.get('videos', [])[:3]:
            print(f"   - {v['product_name']} ({v['status']})")
    
    # Step 9: Analytics
    print("\n📊 Step 9: Getting analytics")
    response = requests.get(
        f"{API_URL}/analytics",
        headers={"X-User-ID": TEST_PHONE}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   Total generations: {data.get('total_generations')}")
        print(f"   Success rate: {data.get('success_rate')}")
    
    print("\n" + "=" * 70)
    print("🎉 Workflow test completed!")
    print(f"📱 Test phone: {TEST_PHONE}")
    print("=" * 70)

if __name__ == "__main__":
    test_full_workflow()
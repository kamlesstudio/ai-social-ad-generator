"""
Test FastAPI Endpoints
"""

import requests
import time
import json
import sys
import os
from pathlib import Path
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"
AUTH_URL = f"{API_URL}/auth"

# Test user phone
TEST_PHONE = "+919999999999"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n📌 {title}")
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
    except:
        print(f"   Response: {response.text[:200]}...")
    return response

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200

def test_send_otp():
    """Test OTP sending"""
    print("\n📱 Testing Send OTP")
    response = requests.post(
        f"{AUTH_URL}/send-otp",
        json={"phone": TEST_PHONE}
    )
    print_response("Send OTP", response)
    if response.status_code == 200:
        data = response.json()
        print(f"   📱 OTP sent to: {data.get('phone')}")
        return True
    return False

def test_verify_otp(otp="123456"):
    """Test OTP verification"""
    print("\n🔑 Testing Verify OTP")
    response = requests.post(
        f"{AUTH_URL}/verify-otp",
        json={"phone": TEST_PHONE, "otp": otp}
    )
    print_response("Verify OTP", response)
    if response.status_code == 200:
        data = response.json()
        print(f"   👤 User: {data.get('user', {}).get('name')}")
        print(f"   🔑 Token: {data.get('access_token', '')[:50]}...")
        return data.get('access_token')
    return None

def test_get_credits(token=None):
    """Test credit balance"""
    print("\n💰 Testing Credit Balance")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(
        f"{API_URL}/credits/balance",
        headers=headers
    )
    print_response("Credit Balance", response)
    return response.json() if response.status_code == 200 else None

def test_generate_video(token=None, auto_complete=False):
    """Test video generation"""
    print(f"\n🎬 Testing Video Generation (Auto-complete: {auto_complete})")
    
    payload = {
        "platform": random.choice(["tiktok", "instagram", "youtube"]),
        "product_name": f"Test Product {random.randint(1, 100)}",
        "product_description": "This is a test product description for AI video generation",
        "duration_seconds": random.choice([4, 6, 8])
    }
    
    endpoint = f"{API_URL}/generate-auto" if auto_complete else f"{API_URL}/generate"
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["Content-Type"] = "application/json"
    headers["X-User-ID"] = TEST_PHONE
    
    response = requests.post(
        endpoint,
        json=payload,
        headers=headers
    )
    print_response("Generate Video", response)
    
    if response.status_code == 200:
        data = response.json()
        task_id = data.get('task_id')
        print(f"   📋 Task ID: {task_id}")
        return task_id
    return None



def test_check_status(task_id, token=None, max_attempts=30):
    """Check video status with longer timeout"""
    print(f"\n📊 Checking Status for: {task_id}")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["X-User-ID"] = TEST_PHONE
    
    for i in range(max_attempts):
        response = requests.get(
            f"{API_URL}/status/{task_id}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            progress = data.get('progress', 0)
            print(f"   [{i+1}] Status: {status}, Progress: {progress}%")
            
            if status == 'completed':
                video_url = data.get('video_url')
                print(f"   ✅ Video URL: {video_url}")
                return True
            elif status == 'failed':
                print(f"   ❌ Error: {data.get('error_message')}")
                return False
            elif status == 'processing':
                # Check if progress is stuck
                if i > 5 and progress < 20:
                    print("   ⚠️ Progress seems stuck, but continuing...")
        
        time.sleep(5)  # Wait 5 seconds between checks
    
    print("   ⏱️ Timeout - Video generation took too long")
    print("   💡 Check the video status manually:")
    print(f"      curl -H 'X-User-ID: {TEST_PHONE}' {API_URL}/status/{task_id}")
    return False



def test_get_user_videos(token=None):
    """Test getting user videos"""
    print("\n📹 Testing Get User Videos")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["X-User-ID"] = TEST_PHONE
    
    response = requests.get(
        f"{API_URL}/user/videos?limit=10",
        headers=headers
    )
    print_response("User Videos", response)
    return response.json() if response.status_code == 200 else None

def test_get_templates():
    """Test getting templates"""
    print("\n📋 Testing Get Templates")
    response = requests.get(f"{API_URL}/templates")
    print_response("Templates", response)
    return response.status_code == 200

def test_analytics(token=None):
    """Test analytics endpoint"""
    print("\n📊 Testing Analytics")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["X-User-ID"] = TEST_PHONE
    
    response = requests.get(
        f"{API_URL}/analytics",
        headers=headers
    )
    print_response("Analytics", response)
    return response.status_code == 200

def test_add_credits(token=None, amount=10):
    """Test adding credits"""
    print(f"\n💰 Adding {amount} credits")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["Content-Type"] = "application/json"
    headers["X-User-ID"] = TEST_PHONE
    
    response = requests.post(
        f"{API_URL}/credits/add?amount={amount}",
        headers=headers
    )
    print_response("Add Credits", response)
    return response.status_code == 200

def run_all_tests():
    """Run all API tests"""
    print("\n" + "=" * 60)
    print("🧪 AI Ad Generator - API Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Server is running")
    except:
        print("❌ Server not running! Start with: uvicorn app.main:app --reload")
        return
    
    # Test 1: Health Check
    test_health()
    
    # Test 2: Templates
    test_get_templates()
    
    # Test 3: OTP Flow
    test_send_otp()
    token = test_verify_otp()
    
    # Test 4: Credits
    if token:
        test_add_credits(token, 20)
        test_get_credits(token)
    
    # Test 5: Generate Video (Auto-complete)
    task_id = test_generate_video(token, auto_complete=True)
    if task_id:
        test_check_status(task_id, token)
    
    # Test 6: Generate Video (Real AI - may take time)
    print("\n" + "=" * 60)
    print("⚠️  Testing Real AI Generation (will take 1-2 minutes)")
    print("=" * 60)
    task_id = test_generate_video(token, auto_complete=False)
    if task_id:
        test_check_status(task_id, token)
    
    # Test 7: Get User Videos
    if token:
        test_get_user_videos(token)
        test_analytics(token)
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
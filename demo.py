"""
Quick demo script for your AI Ad Generator API
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def demo():
    print("🎬 AI Social Media Ad Generator Demo")
    print("=" * 50)
    
    # 1. Check health
    print("\n1️⃣ Checking API health...")
    health = requests.get(f"{BASE_URL}/health")
    print(f"   ✅ API is {health.json()['status']}")
    
    # 2. Generate video
    print("\n2️⃣ Generating video...")
    response = requests.post(f"{BASE_URL}/api/v1/generate", json={
        "platform": "tiktok",
        "product_name": "Smart Fitness Watch Pro",
        "product_description": "AI-powered fitness tracker with 24/7 heart monitoring",
        "duration_seconds": 10
    })
    task_id = response.json()["task_id"]
    print(f"   📝 Task ID: {task_id}")
    print(f"   💰 Credits used: {response.json()['credits_used']}")
    
    # 3. Check status until complete
    print("\n3️⃣ Waiting for generation...")
    while True:
        status = requests.get(f"{BASE_URL}/api/v1/status/{task_id}").json()
        print(f"   Progress: {status.get('progress', 0)}% - Status: {status['status']}")
        
        if status["status"] == "completed":
            print(f"\n   🎉 Video ready!")
            print(f"   📹 URL: {status['video_url']}")
            break
        elif status["status"] == "failed":
            print(f"\n   ❌ Error: {status.get('error_message')}")
            break
        time.sleep(2)
    
    # 4. Check credits
    print("\n4️⃣ Credit balance...")
    credits = requests.get(f"{BASE_URL}/api/v1/credits/balance").json()
    print(f"   💰 Balance: {credits['balance']} credits")
    
    # 5. List all tasks
    print("\n5️⃣ Recent tasks...")
    tasks = requests.get(f"{BASE_URL}/api/v1/tasks").json()
    print(f"   📊 Total tasks: {tasks['total_tasks']}")
    for task in tasks['tasks'][:3]:
        print(f"   - {task['product']} ({task['status']})")
    
    print("\n" + "=" * 50)
    print("✅ Demo complete! Your AI Ad Generator is working!")

if __name__ == "__main__":
    demo()
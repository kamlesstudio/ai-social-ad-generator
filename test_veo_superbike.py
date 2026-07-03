"""
Veo 3 Superbike Video Generation
Testing with high-quality superbike prompts
"""

import time
from google import genai
from google.genai import types

def generate_superbike_video(prompt, duration=6, aspect_ratio="16:9"):
    PROJECT_ID = "ai-social-ad-generator"
    LOCATION = "us-central1"
    BUCKET = "ai-ad-videos-kamlesh-2026"
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # Use the GA model (confirmed working)
    model_id = "veo-3.1-generate-001"
    
    # Create a unique timestamped path
    timestamp = int(time.time())
    output_path = f"gs://{BUCKET}/superbike_outputs/{timestamp}/"

    print(f"🏍️ Starting superbike generation...")
    print(f"📝 Prompt: {prompt[:100]}...")
    print(f"📁 Output path: {output_path}")
    
    try:
        operation = client.models.generate_videos(
            model=model_id,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration,
                output_gcs_uri=output_path,
            ),
        )

        print(f"⏳ Operation started, polling...")
        
        # Poll until complete (2-3 minutes)
        start_time = time.time()
        while not operation.done:
            time.sleep(20)
            operation = client.operations.get(operation)
            elapsed = int(time.time() - start_time)
            print(f"  ... {elapsed}s elapsed")

        if operation.error:
            print(f"\n❌ Error: {operation.error}")
            return None

        if operation.result and operation.result.generated_videos:
            video_uri = operation.result.generated_videos[0].video.uri
            print(f"\n✅ SUCCESS!")
            print(f"📹 Video: {video_uri}")
            public_url = video_uri.replace("gs://", "https://storage.googleapis.com/")
            print(f"🔗 Watch here: {public_url}")
            return public_url
        else:
            print("\n⚠️ No video found.")
            return None

    except Exception as e:
        print(f"\n❌ SDK Error: {e}")
        return None

def test_superbike_prompts():
    """Test multiple superbike prompts"""
    
    # Superbike Prompts
    prompts = [
        {
            "name": "Ducati Panigale V4",
            "prompt": "A stunning Ducati Panigale V4 superbike parked on a scenic mountain road at sunset. Golden hour lighting, dramatic shadows, the bike's red paint glistening. Camera slowly orbits around the bike, capturing every detail. 4k cinematic quality."
        },
        {
            "name": "Kawasaki Ninja H2R",
            "prompt": "A Kawasaki Ninja H2R racing through a winding mountain pass at high speed. Motion blur, the green and black livery cutting through the mist. Dynamic camera angle from low to the ground, capturing the speed and power. Cinematic, adrenaline-filled action."
        },
        {
            "name": "BMW M1000RR Studio",
            "prompt": "A BMW M1000RR superbike in a professional photography studio. Softbox lighting, pure white background, the bike perfectly illuminated. Every detail visible - carbon fiber parts, Brembo brakes, racing exhaust. Ultra HD 4k, commercial photography style."
        },
        {
            "name": "Night Cyberpunk",
            "prompt": "A futuristic electric superbike riding through neon-lit Tokyo streets at night. Reflections on wet roads, glowing LED accents on the bike. Cyberpunk aesthetic, 8k quality, cinematic lighting with purple and blue neon tones."
        },
        {
            "name": "Action Racing",
            "prompt": "A superbike racing on a professional track, leaning into a sharp corner at high speed. Sparks flying from the footpegs, the rider in full leather racing suit. Dynamic camera following the bike, capturing the adrenaline. Professional racing footage style."
        }
    ]
    
    print("🏍️" * 30)
    print("   VEO 3 - SUPERBIKE VIDEO GENERATOR")
    print("🏍️" * 30 + "\n")
    
    print("Select a superbike prompt:")
    for i, p in enumerate(prompts, 1):
        print(f"  {i}. {p['name']}")
    print("  6. Generate ALL (takes ~15 minutes)")
    print("  7. Exit")
    
    try:
        choice = input("\nSelect (1-7): ").strip()
        if not choice:
            choice = "1"
        choice = int(choice)
    except:
        choice = 1
    
    if choice == 7:
        print("Exiting...")
        return
    
    if choice == 6:
        # Generate all
        print("\n🏍️ Generating ALL videos (this will take ~15 minutes)...")
        results = []
        for i, p in enumerate(prompts, 1):
            print(f"\n--- [{i}/{len(prompts)}] {p['name']} ---")
            url = generate_superbike_video(p["prompt"], duration=6, aspect_ratio="16:9")
            if url:
                results.append((p["name"], url))
            time.sleep(5)  # Small delay between requests
        
        print("\n" + "=" * 60)
        print("🎉 ALL COMPLETE!")
        for name, url in results:
            print(f"🏍️ {name}: {url}")
        print("=" * 60)
        return
    
    if 1 <= choice <= 5:
        selected = prompts[choice - 1]
        print(f"\n🏍️ Generating: {selected['name']}")
        generate_superbike_video(selected["prompt"], duration=6, aspect_ratio="16:9")
    else:
        print("Invalid selection")

if __name__ == "__main__":
    test_superbike_prompts()
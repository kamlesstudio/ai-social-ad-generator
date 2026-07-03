import time
from google import genai
from google.genai import types

def run_veo_ga():
    PROJECT_ID = "ai-social-ad-generator"
    LOCATION = "us-central1"
    BUCKET = "ai-ad-videos-kamlesh-2026"
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # Use the current GA model ID
    model_id = "veo-3.1-generate-001" 
    prompt = "A futuristic underwater city with glowing lights and submarines."
    output_path = f"gs://{BUCKET}/veo_ga_outputs/{int(time.time())}/"

    print(f"🎬 Starting generation with: {model_id}")
    print(f"📁 Output path: {output_path}")
    
    try:
        operation = client.models.generate_videos(
            model=model_id,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                aspect_ratio="16:9",
                duration_seconds=6,
                output_gcs_uri=output_path,
            ),
        )

        print(f"⏳ Operation: {operation.name}")
        print("Polling (takes 2-3 minutes)...")
        
        # Poll until complete (typically 2-3 minutes)
        start_time = time.time()
        while not operation.done:
            time.sleep(20)
            operation = client.operations.get(operation)
            elapsed = int(time.time() - start_time)
            print(f"  ... {elapsed}s elapsed")

        if operation.error:
            print(f"\n❌ Error: {operation.error}")
            return

        # Path to extract the video URI for Veo 3.1 GA
        if operation.result and operation.result.generated_videos:
            video_uri = operation.result.generated_videos[0].video.uri
            print(f"\n✅ Success! Video: {video_uri}")
            public_url = video_uri.replace("gs://", "https://storage.googleapis.com/")
            print(f"🔗 Public Link: {public_url}")
        else:
            print("\n⚠️ No video found in the result metadata.")
            print("Check your bucket directly:")
            print(f"gsutil ls {output_path}")

    except Exception as e:
        print(f"\n❌ SDK Error: {e}")

if __name__ == "__main__":
    run_veo_ga()
import requests

url = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
response = requests.get(url, stream=True)

with open("sample.mp4", "wb") as file:
    for chunk in response.iter_content(chunk_size=8192):
        file.write(chunk)

print("✅ Video downloaded successfully!")
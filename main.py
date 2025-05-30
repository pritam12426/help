# zed is how able to work with screen short

# pip install google-generativeai=0.8.5 

import os
import time
import hashlib
import subprocess
from dotenv import load_dotenv
from google import generativeai as genai
import platform

# Check platform compatibility
if platform.system() != "Darwin":
    raise EnvironmentError("⚠️ This script only runs on macOS due to 'screencapture' and 'pbcopy' dependencies.")

# Setup
load_dotenv()
KEY = os.getenv("KEY")
if not KEY:
    raise EnvironmentError("❌ API key not found in .env file (KEY=...)")
genai.configure(api_key=KEY)

WATCH_DIR = "/Users/pritam/cheating"
LOCAL_SCREEN_SHORT = "/Users/pritam/Pictures/screen_short/exam/cse48d"
SCREENSHOT_FILE = os.path.join(WATCH_DIR, "screenshot.png")
os.makedirs(LOCAL_SCREEN_SHORT, exist_ok=True)

# Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")
PROMPT = "I have provided a question, please generate the corresponding answers for each question without additional explanations. Ensure that the answers are accurate and concise, matching the format of multiple-choice or fill-in-the-blank as required by each question."

def md5_hash(filepath: str):
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).digest()
    except FileNotFoundError:
        return None

def take_screenshot(path: str):
    result = subprocess.run(["screencapture", "-sx", path])
    return result.returncode == 0

def query_gemini(image_path: str):
    with open(image_path, "rb") as f:
        image_data = f.read()

    response = model.generate_content(
        contents=[{
            "role": "user",
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": "image/png", "data": image_data}},
            ],
        }]
    )
    return response.text

def main():
    counter = 1
    while True:
        print(f"📸 Taking screenshot {counter}: screenshot.png")

        if not take_screenshot(SCREENSHOT_FILE):
            print("❌ Failed to take screenshot.")
            time.sleep(5)
            continue

        time.sleep(0.2)  # Allow filesystem to catch up

        local_copy = os.path.join(LOCAL_SCREEN_SHORT, f"Q-No-{counter}.png")

        current_hash = md5_hash(SCREENSHOT_FILE)
        previous_hash = md5_hash(local_copy)

        if current_hash == previous_hash:
            print("⚠️ Duplicate image detected. Skipping...")
        else:
            subprocess.run(["cp", "-p", SCREENSHOT_FILE, local_copy])
            print("🧠 Sending image to Gemini...")
            try:
                answer = query_gemini(SCREENSHOT_FILE)
                if answer:
                    subprocess.run(["pbcopy"], input=answer.encode())
                    print(f"✅ Answer    -> {answer.encode()}")
                    print("📋 Answer copied to clipboard.")
                    subprocess.run(["say"], input=answer.encode())
                    # todo: add sound to this ans user eairphone
                else:
                    print("⚠️ Gemini returned no answer.")
            except Exception as e:
                print(f"🚨 Gemini error: {type(e).__name__}: {e}")
            counter += 1

        print(f"✅ Screenshot {counter - 1} processed. Waiting for next...")
        time.sleep(5)

if __name__ == "__main__":
    time.sleep(7)
    main()

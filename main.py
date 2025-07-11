# https://aistudio.google.com/app/apikey
"""
touch .env
python3 -m venv venv
source venv/bin/activate
pip install google-generativeai=0.8.5
python ./main.py
"""

""" .env should be like this
KEY = "xxxxxx"
"""

import os
import logging
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

TEMP_DIR = os.getenv("TMPDIR")
WATCH_DIR = TEMP_DIR + "/cheating"
LOCAL_SCREEN_SHORT = TEMP_DIR + "/cheating-backup"
SCREENSHOT_FILE = os.path.join(WATCH_DIR, "screenshot.png")
os.makedirs(LOCAL_SCREEN_SHORT, exist_ok=True)
os.makedirs(WATCH_DIR, exist_ok=True)

# Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")
# PROMPT = "I have provided a question, please generate the corresponding answers for each question without additional explanations. Ensure that the answers are accurate and concise, matching the format of multiple-choice or fill-in-the-blank as required by each question."
PROMPT = """I have provided a question. Please generate the corresponding answer(s) without any additional explanation.
If the question includes multiple-choice options, return concise and accurate answers.
If the options do not have explicit labels (like A, B, C, or 1, 2, 3, 4) in the image, assume they follow the order 1, 2, 3, 4 by default and use these numbers in your answer.
Format the answer appropriately for multiple-choice or fill-in-the-blank questions as needed."""

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

# Configure logging once at the top of your script
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

def main():
    counter = 1
    last_hash = None

    try:
        while True:
            logging.info(f"📸 Taking screenshot {counter}: screenshot.png")

            if not take_screenshot(SCREENSHOT_FILE):
                logging.error("❌ Failed to take screenshot.")
                time.sleep(5)
                continue

            time.sleep(0.2)  # Allow filesystem to catch up

            current_hash = md5_hash(SCREENSHOT_FILE)

            if current_hash == last_hash:
                logging.warning("⚠️ Duplicate image detected. Skipping...")
            else:
                local_copy = os.path.join(LOCAL_SCREEN_SHORT, f"Q-No-{counter}.png")
                subprocess.run(["cp", "-p", SCREENSHOT_FILE, local_copy])
                logging.info("🧠 Sending image to Gemini...")

                try:
                    answer = query_gemini(SCREENSHOT_FILE)
                    if answer:
                        subprocess.run(["pbcopy"], input=answer.encode())
                        logging.info(f"✅ Answer copied to clipboard. -> {answer}")
                        os.system(f"say {answer}")
                        command = ['osascript', '-e', f'tell app "System Events" to display dialog "{answer}"']
                        subprocess.run(command)
                    else:
                        logging.warning("⚠️ Gemini returned no answer.")
                except Exception as e:
                    logging.exception(f"🚨 Gemini error: {type(e).__name__}: {e}")

                last_hash = current_hash
                counter += 1

            logging.info(f"✅ Screenshot {counter - 1} processed. Waiting for next...")
            time.sleep(5)

    except KeyboardInterrupt:
        logging.info("👋 Exiting gracefully.")


if __name__ == "__main__":
    time.sleep(7)
    main()

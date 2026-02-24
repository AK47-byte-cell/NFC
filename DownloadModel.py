import os
from faster_whisper import download_model

MODEL_NAME = "large-v3"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "models")

print(f"Downloading {MODEL_NAME} model for offline use...")
download_model(MODEL_NAME, output_dir=DOWNLOAD_DIR)
print(f"\n✅ Download complete. Model saved to: {DOWNLOAD_DIR}")

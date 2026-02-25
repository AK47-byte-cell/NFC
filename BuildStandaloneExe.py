import os
import shutil
import subprocess
import sys

from faster_whisper import download_model

MODEL_NAME = "large-v3"
ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ROOT, "models")
DIST_APP_DIR = os.path.join(ROOT, "dist", "AudioTranscriber")


def run(cmd):
    print(f"\n[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def ensure_model_downloaded():
    if os.path.isdir(MODELS_DIR) and os.listdir(MODELS_DIR):
        print(f"Model already present at: {MODELS_DIR}")
        return

    print(f"Downloading {MODEL_NAME} model for offline use...")
    download_model(MODEL_NAME, output_dir=MODELS_DIR)
    print(f"✅ Download complete. Model saved to: {MODELS_DIR}")


def build_exe():
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconsole",
            "--collect-all",
            "faster_whisper",
            "--collect-all",
            "ctranslate2",
            "--collect-all",
            "tkinterdnd2",
            "AudioTranscriber.py",
        ]
    )


def bundle_model():
    if not os.path.isdir(DIST_APP_DIR):
        raise FileNotFoundError(f"Build output not found: {DIST_APP_DIR}")

    dist_models_dir = os.path.join(DIST_APP_DIR, "models")
    if os.path.exists(dist_models_dir):
        shutil.rmtree(dist_models_dir)
    shutil.copytree(MODELS_DIR, dist_models_dir)
    print(f"✅ Copied models to: {dist_models_dir}")


def main():
    os.chdir(ROOT)
    ensure_model_downloaded()
    build_exe()
    bundle_model()
    print("\n✅ Done. Standalone app is ready at: dist\\AudioTranscriber")


if __name__ == "__main__":
    main()

# Offline Deposition Transcriber Build Instructions

This guide packages a standalone, fully offline transcription tool for legal proceedings and depositions.

## Phase 1: Environment Setup & Dependencies

Run on a Windows machine with Python 3 in PATH and internet access for initial setup.

1. `py -m pip install --upgrade pip`
2. `py -m pip install faster-whisper pyinstaller`
3. Create a staging directory: `C:\TranscriptionSetup\`
4. Copy `DownloadModel.py` and `AudioTranscriber.py` into `C:\TranscriptionSetup\`

## Phase 2: Download the Local Model

1. Open Command Prompt in `C:\TranscriptionSetup\`
2. Run `py DownloadModel.py`
3. Confirm a `models` folder is created and populated

## Phase 3: Build the Standalone Executable

From `C:\TranscriptionSetup\` run:

```bat
pyinstaller --noconsole --collect-all faster_whisper --collect-all ctranslate2 AudioTranscriber.py
```

Then:

1. Open `dist\AudioTranscriber\`
2. Move/copy `models` into `dist\AudioTranscriber\` so it sits beside `AudioTranscriber.exe`

## Phase 4: Final Deployment

1. Move `dist\AudioTranscriber\` to `C:\Program Files\` (or approved local app directory)
2. Create a Desktop shortcut for `AudioTranscriber.exe`
3. Remove `C:\TranscriptionSetup\` when finished

## Security Notes

- Runtime is fully local and does not require cloud APIs
- Model inference is pinned to CPU (`compute_type="int8"`) for stability on Lenovo Yoga 9i-class hardware
- No external data transmission is required after packaging

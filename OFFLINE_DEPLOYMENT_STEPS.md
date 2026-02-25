# Offline Deposition Transcriber Build Instructions

If you want it to just build the `.exe`, run one command from this folder:

```bat
make_exe.bat
```

This will:

1. Install required packages (`faster-whisper`, `pyinstaller`, `tkinterdnd2`)
2. Download the local `large-v3` model (if not already present)
3. Build `AudioTranscriber.exe` with drag-and-drop support
4. Copy `models` next to the `.exe` inside `dist\AudioTranscriber`

## Files

- `AudioTranscriber.py`: offline GUI transcription app with drag-and-drop, improved styling, and progress indicator
- `BuildStandaloneExe.py`: one-shot Python build script
- `make_exe.bat`: Windows launcher script for setup + build

## Output

Final standalone app folder:

`dist\AudioTranscriber`

Move that folder to your approved local install location and create a desktop shortcut to `AudioTranscriber.exe`.

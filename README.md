## Local Audio Transcriber (Windows, Offline)

This project gives you a **local audio-to-text workflow** with:

- Drag-and-drop GUI queue.
- One-file or batch transcription.
- Right-click action in Windows Explorer to transcribe a single file.
- Output `.txt` written in the **same folder** as the source audio/video file.
- Good handling for long recordings using `faster-whisper` streaming segments + VAD.
- English/French automatic language detection.


## Git workflow

See [BRANCHING.md](BRANCHING.md) for the recommended branch naming and release workflow for this project.

---

## Why this setup matches your machine

Your Lenovo Yoga with **Intel Core Ultra 7 + 32 GB RAM + Intel Arc iGPU** is a strong fit for local transcription.

Default settings in this app use:

- Model: `large-v3` (high accuracy)
- Device: `auto`
- Compute type: `int8_float16`

If memory/performance is tight, run with `--model medium` first.

---

## 1) Install prerequisites (Windows 11)

1. Install **Python 3.11+** (and check "Add python to PATH").
2. Install **FFmpeg** and ensure `ffmpeg.exe` is in PATH.
3. Open PowerShell in this repo and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2) Launch the GUI

```powershell
python transcriber_app\transcribe_gui.py
```

Use:

- **Drag files** into the list (if `tkinterdnd2` is installed).
- **Add Files** button as fallback.
- **Transcribe Selected** or **Transcribe All**.
- Right-click selected rows in the app for quick actions.

Generated transcript path example:

- `D:\Recordings\Interview01.mp3` -> `D:\Recordings\Interview01.txt`

---

## 3) Enable Windows Explorer right-click: “Transcribe audio to text”

Inside this repo, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_context_menu.ps1 -PythonExe ".\.venv\Scripts\python.exe"
```

After that, right-click a file in Explorer and choose **Transcribe audio to text**.

It runs:

```powershell
python transcriber_app\transcribe_gui.py --file "<your-file>"
```

and writes the `.txt` beside the source file.

---

## Optional tuning for long recordings

For many-hour files, this app already enables VAD segmentation. You can tune model/runtime:

```powershell
python transcriber_app\transcribe_gui.py --model medium --compute-type int8 --device cpu
```

Common tradeoffs:

- `large-v3`: best accuracy, slower.
- `medium`: faster, still strong.
- `int8`: lower memory.

---

## Notes

- Fully local/offline after models are downloaded once.
- First run downloads model weights.
- No cloud API is required.

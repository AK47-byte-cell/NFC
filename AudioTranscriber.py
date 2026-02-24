import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext

from faster_whisper import WhisperModel

MODEL_NAME = "large-v3"
DEVICE = "cpu"
COMPUTE = "int8"
model = None


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def transcribe_file(audio_path):
    print(f"\nTranscribing: {audio_path}")
    print("-" * 50)

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        temperature=0.0,
        initial_prompt="Bonjour. Hello. Proceeding with the deposition. Déposition en cours.",
    )

    output_path = os.path.splitext(audio_path)[0] + ".txt"

    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            text = segment.text.strip() + " "
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text.strip()}")

    print(f"\nSaved: {output_path}")
    print("-" * 50)


def process_paths(paths):
    global model
    if model is None:
        print("Loading offline Whisper model into memory... (Please wait)")
        local_model_path = os.path.join(get_base_path(), "models")
        model = WhisperModel(local_model_path, device=DEVICE, compute_type=COMPUTE)
        print("Model loaded successfully.\n")

    for path in paths:
        if os.path.isfile(path):
            try:
                transcribe_file(path)
            except Exception as e:
                print(f"\n[ERROR] Failed: {e}")
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith((".mp3", ".wav", ".m4a", ".flac")):
                        try:
                            transcribe_file(os.path.join(root, file))
                        except Exception as e:
                            print(f"\n[ERROR] Failed: {e}")
    print("\n✅ All processing complete.")


class PrintRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.after(0, self._write_to_widget, text)

    def _write_to_widget(self, text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass


def run_in_background(paths):
    thread = threading.Thread(target=process_paths, args=(paths,))
    thread.daemon = True
    thread.start()


def select_files():
    files = filedialog.askopenfilenames(
        filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.flac")]
    )
    if files:
        run_in_background(files)


def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        run_in_background([folder])


def create_gui():
    root = tk.Tk()
    root.title("Offline Deposition Transcriber")
    root.geometry("750x500")
    root.configure(padx=20, pady=20)

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill=tk.X, pady=(0, 15))
    tk.Button(
        btn_frame,
        text="Select File(s)",
        command=select_files,
        width=20,
        height=2,
        font=("Arial", 10, "bold"),
    ).pack(side=tk.LEFT, padx=(0, 10))
    tk.Button(
        btn_frame,
        text="Select Folder (Batch)",
        command=select_folder,
        width=20,
        height=2,
        font=("Arial", 10, "bold"),
    ).pack(side=tk.LEFT)

    tk.Label(root, text="Transcription Progress:", font=("Arial", 10)).pack(anchor=tk.W)
    console_text = scrolledtext.ScrolledText(
        root, wrap=tk.WORD, font=("Consolas", 10), state="disabled"
    )
    console_text.pack(fill=tk.BOTH, expand=True)

    sys.stdout = sys.stderr = PrintRedirector(console_text)
    print("System ready. 100% Offline Mode. Select files or a folder to begin.")
    root.mainloop()


if __name__ == "__main__":
    create_gui()

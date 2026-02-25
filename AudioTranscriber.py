import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

from faster_whisper import WhisperModel

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    DND_FILES = None
    TkinterDnD = None

MODEL_NAME = "large-v3"
DEVICE = "cpu"
COMPUTE = "int8"
SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".m4a", ".flac")

model = None
is_processing = False
root = None
console_text = None
progress_bar = None
status_var = None
select_files_btn = None
select_folder_btn = None


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def transcribe_file(audio_path):
    print(f"\nTranscribing: {audio_path}")
    print("-" * 50)

    segments, info = model.transcribe(
        audio_path,
        beam_size=2,  # Lowered from 5 to prevent memory spikes
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
            # Removed os.fsync(f.fileno()) to prevent SSD bottlenecking
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text.strip()}")

    print(f"\nDetected language: {info.language} (p={info.language_probability:.2f})")
    print(f"Saved: {output_path}")
    print("-" * 50)


def process_paths(paths):
    global model
    if model is None:
        print("Loading offline Whisper model into memory... (Please wait)")
        local_model_path = os.path.join(get_base_path(), "models")
        # Added cpu_threads=4 to prevent hybrid core crashes
        model = WhisperModel(
            local_model_path, device=DEVICE, compute_type=COMPUTE, cpu_threads=4
        )
        print("Model loaded successfully.\n")

    for path in paths:
        if os.path.isfile(path):
            try:
                transcribe_file(path)
            except Exception as e:
                print(f"\n[ERROR] Failed: {e}")
        elif os.path.isdir(path):
            for root_dir, _, files in os.walk(path):
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        full_path = os.path.join(root_dir, file_name)
                        try:
                            transcribe_file(full_path)
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


def _set_processing_state(active):
    global is_processing
    is_processing = active

    if active:
        status_var.set("Processing audio…")
        progress_bar.start(12)
        select_files_btn.configure(state="disabled")
        select_folder_btn.configure(state="disabled")
    else:
        status_var.set("Ready. Drop files/folders or choose a selection.")
        progress_bar.stop()
        select_files_btn.configure(state="normal")
        select_folder_btn.configure(state="normal")


def run_in_background(paths):
    if is_processing:
        print("\n[INFO] A transcription job is already running.")
        return

    _set_processing_state(True)

    def worker():
        try:
            process_paths(paths)
        finally:
            root.after(0, lambda: _set_processing_state(False))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def select_files():
    files = filedialog.askopenfilenames(
        filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.flac")]
    )
    if files:
        run_in_background(list(files))


def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        run_in_background([folder])


def _handle_drop(event):
    items = root.tk.splitlist(event.data)
    normalized = []

    for item in items:
        cleaned = item.strip().strip("{}")
        if os.path.exists(cleaned):
            normalized.append(cleaned)

    if not normalized:
        print("\n[WARN] Dropped item was not a valid local path.")
        return

    run_in_background(normalized)


def create_gui():
    global root
    global console_text
    global progress_bar
    global status_var
    global select_files_btn
    global select_folder_btn

    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    root.title("Offline Deposition Transcriber")
    root.geometry("900x620")
    root.minsize(820, 560)
    root.configure(bg="#0f172a", padx=20, pady=20)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Main.TFrame", background="#0f172a")
    style.configure("Card.TFrame", background="#111827", borderwidth=0)
    style.configure("Title.TLabel", background="#0f172a", foreground="#e5e7eb", font=("Segoe UI", 18, "bold"))
    style.configure("Sub.TLabel", background="#0f172a", foreground="#94a3b8", font=("Segoe UI", 10))
    style.configure("Status.TLabel", background="#0f172a", foreground="#cbd5e1", font=("Segoe UI", 10, "bold"))
    style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"), padding=10)
    style.map("Modern.TButton", background=[("active", "#1d4ed8")], foreground=[("active", "white")])
    style.configure("Green.Horizontal.TProgressbar", troughcolor="#1f2937", bordercolor="#1f2937", background="#22c55e", lightcolor="#22c55e", darkcolor="#22c55e")

    main = ttk.Frame(root, style="Main.TFrame")
    main.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main, text="Offline Deposition Transcriber", style="Title.TLabel").pack(anchor=tk.W)
    ttk.Label(
        main,
        text="Secure local processing • CPU int8 mode • No cloud API",
        style="Sub.TLabel",
    ).pack(anchor=tk.W, pady=(0, 14))

    controls = ttk.Frame(main, style="Main.TFrame")
    controls.pack(fill=tk.X, pady=(0, 10))

    select_files_btn = ttk.Button(
        controls,
        text="Select File(s)",
        command=select_files,
        style="Modern.TButton",
    )
    select_files_btn.pack(side=tk.LEFT, padx=(0, 10))

    select_folder_btn = ttk.Button(
        controls,
        text="Select Folder (Batch)",
        command=select_folder,
        style="Modern.TButton",
    )
    select_folder_btn.pack(side=tk.LEFT)

    drop_zone = tk.Label(
        main,
        text=(
            "Drag & drop files/folders here"
            if DND_AVAILABLE
            else "Install tkinterdnd2 to enable drag & drop"
        ),
        bg="#111827",
        fg="#d1d5db",
        relief="groove",
        bd=2,
        padx=12,
        pady=18,
        font=("Segoe UI", 11, "bold"),
    )
    drop_zone.pack(fill=tk.X, pady=(0, 12))

    if DND_AVAILABLE:
        drop_zone.drop_target_register(DND_FILES)
        drop_zone.dnd_bind("<<Drop>>", _handle_drop)

    status_var = tk.StringVar(value="Ready. Drop files/folders or choose a selection.")
    ttk.Label(main, textvariable=status_var, style="Status.TLabel").pack(anchor=tk.W)

    progress_bar = ttk.Progressbar(
        main,
        mode="indeterminate",
        style="Green.Horizontal.TProgressbar",
    )
    progress_bar.pack(fill=tk.X, pady=(6, 14))

    console_text = scrolledtext.ScrolledText(
        main,
        wrap=tk.WORD,
        font=("Consolas", 10),
        state="disabled",
        bg="#020617",
        fg="#e2e8f0",
        insertbackground="#e2e8f0",
        relief="flat",
        padx=10,
        pady=10,
    )
    console_text.pack(fill=tk.BOTH, expand=True)

    sys.stdout = sys.stderr = PrintRedirector(console_text)
    print("System ready. 100% Offline Mode. Select or drag files/folders to begin.")

    root.mainloop()


if __name__ == "__main__":
    create_gui()

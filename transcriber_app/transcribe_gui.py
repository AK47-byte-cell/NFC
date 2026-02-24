from __future__ import annotations

import argparse
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    DND_FILES = None
    TkinterDnD = None

from faster_whisper import WhisperModel

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".aac",
    ".ogg",
    ".wma",
    ".mp4",
    ".mkv",
    ".mov",
}


@dataclass
class AppConfig:
    model_name: str = "large-v3"
    compute_type: str = "int8_float16"
    device: str = "auto"


class Transcriber:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._model: WhisperModel | None = None

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.config.model_name,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )
        return self._model

    def transcribe_file(self, file_path: Path) -> Path:
        segments, info = self.model.transcribe(
            str(file_path),
            language=None,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 700},
            condition_on_previous_text=True,
            word_timestamps=False,
            temperature=0.0,
        )
        text_lines = []
        for segment in segments:
            line = segment.text.strip()
            if line:
                text_lines.append(line)

        output_path = file_path.with_suffix(".txt")
        content = "\n".join(text_lines).strip() + "\n"
        output_path.write_text(content, encoding="utf-8")
        return output_path


def parse_dropped_files(raw_event_data: str) -> Iterable[Path]:
    # Handles paths like {C:/My File.wav} {D:/Another.mp3}
    current = ""
    in_braces = False
    for ch in raw_event_data.strip():
        if ch == "{":
            in_braces = True
            current = ""
            continue
        if ch == "}":
            in_braces = False
            if current:
                yield Path(current)
            current = ""
            continue
        if ch == " " and not in_braces:
            if current:
                yield Path(current)
                current = ""
            continue
        current += ch
    if current:
        yield Path(current)


class TranscribeApp:
    def __init__(self, root: tk.Tk, transcriber: Transcriber) -> None:
        self.root = root
        self.transcriber = transcriber
        self.files: list[Path] = []
        self.progress_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._is_running = False

        self.root.title("Local Audio Transcriber")
        self.root.geometry("900x550")

        self._build_ui()
        self._poll_progress()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        instructions = ttk.Label(
            container,
            text=(
                "Drag audio/video files here or use Add Files. "
                "Right-click items for quick actions.\n"
                "Transcriptions are written as .txt in the same folder as each source file."
            ),
            justify=tk.LEFT,
        )
        instructions.pack(fill=tk.X, pady=(0, 10))

        self.file_listbox = tk.Listbox(container, selectmode=tk.EXTENDED)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<Button-3>", self._show_context_menu)

        if DND_FILES is not None and hasattr(self.file_listbox, "drop_target_register"):
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind("<<Drop>>", self._on_drop)

        toolbar = ttk.Frame(container)
        toolbar.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(toolbar, text="Add Files", command=self.add_files_dialog).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Transcribe Selected", command=self.transcribe_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="Transcribe All", command=self.transcribe_all).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="Clear", command=self.clear_all).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(container, textvariable=self.status_var).pack(fill=tk.X, pady=(8, 0))

    def _show_context_menu(self, event: tk.Event) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Transcribe selected", command=self.transcribe_selected)
        menu.add_command(label="Remove selected", command=self.remove_selected)
        menu.tk_popup(event.x_root, event.y_root)

    def _on_drop(self, event: tk.Event) -> None:
        raw = getattr(event, "data", "")
        self.add_paths(parse_dropped_files(raw))

    def add_files_dialog(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select audio/video files",
            filetypes=[("Media files", "*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma *.mp4 *.mkv *.mov"), ("All files", "*.*")],
        )
        self.add_paths(Path(x) for x in files)

    def add_paths(self, paths: Iterable[Path]) -> None:
        added = 0
        for path in paths:
            candidate = Path(path)
            if not candidate.exists() or candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if candidate not in self.files:
                self.files.append(candidate)
                self.file_listbox.insert(tk.END, str(candidate))
                added += 1
        self.status_var.set(f"Added {added} file(s). Total queue: {len(self.files)}")

    def _selection_paths(self) -> list[Path]:
        indices = self.file_listbox.curselection()
        return [self.files[i] for i in indices]

    def remove_selected(self) -> None:
        indices = sorted(self.file_listbox.curselection(), reverse=True)
        for idx in indices:
            del self.files[idx]
            self.file_listbox.delete(idx)
        self.status_var.set(f"Removed {len(indices)} file(s).")

    def clear_all(self) -> None:
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.status_var.set("Queue cleared.")

    def transcribe_selected(self) -> None:
        selected = self._selection_paths()
        if not selected:
            messagebox.showinfo("No selection", "Please select at least one file.")
            return
        self._start_background(selected)

    def transcribe_all(self) -> None:
        if not self.files:
            messagebox.showinfo("No files", "Please add one or more files.")
            return
        self._start_background(list(self.files))

    def _start_background(self, batch: list[Path]) -> None:
        if self._is_running:
            messagebox.showwarning("Busy", "A transcription job is already running.")
            return

        self._is_running = True
        self.status_var.set(f"Starting transcription for {len(batch)} file(s)...")

        def work() -> None:
            try:
                for index, path in enumerate(batch, start=1):
                    self.progress_queue.put(("status", f"[{index}/{len(batch)}] Transcribing: {path.name}"))
                    output = self.transcriber.transcribe_file(path)
                    self.progress_queue.put(("status", f"Done: {output}"))
                self.progress_queue.put(("done", f"Finished {len(batch)} file(s)."))
            except Exception as exc:  # noqa: BLE001
                self.progress_queue.put(("error", str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _poll_progress(self) -> None:
        try:
            while True:
                kind, payload = self.progress_queue.get_nowait()
                if kind == "status":
                    self.status_var.set(payload)
                elif kind == "done":
                    self._is_running = False
                    self.status_var.set(payload)
                    messagebox.showinfo("Complete", payload)
                elif kind == "error":
                    self._is_running = False
                    self.status_var.set(f"Failed: {payload}")
                    messagebox.showerror("Transcription failed", payload)
        except queue.Empty:
            pass
        self.root.after(250, self._poll_progress)


def transcribe_single_file(file_path: Path, config: AppConfig) -> Path:
    transcriber = Transcriber(config)
    return transcriber.transcribe_file(file_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local audio transcription GUI + CLI helper")
    parser.add_argument("--file", type=Path, help="Run one-shot transcription for a single file and exit")
    parser.add_argument("--model", default="large-v3", help="faster-whisper model name")
    parser.add_argument("--device", default="auto", help="Device: auto/cpu/cuda")
    parser.add_argument("--compute-type", default="int8_float16", help="Compute type (ex: int8, int8_float16, float16)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig(model_name=args.model, device=args.device, compute_type=args.compute_type)

    if args.file:
        source = args.file.expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        output = transcribe_single_file(source, config)
        print(f"Wrote transcription: {output}")
        return

    if TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = TranscribeApp(root, Transcriber(config))
    if TkinterDnD is None:
        app.status_var.set("Install tkinterdnd2 for drag-and-drop support (GUI still works with Add Files).")
    root.mainloop()


if __name__ == "__main__":
    main()

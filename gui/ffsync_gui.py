#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tkinter wrapper for the original ffsubsync script.

It simply launches the bundled ffsubsync.py with the video, subtitle
and optional offset the user selects.  All output is shown in a small
pop‑up so you know whether the sync succeeded or failed.
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# ----------------------------------------------------------------------
# Locate the ffsubsync script that was added as a data file by PyInstaller.
# ----------------------------------------------------------------------
def _ffsubsync_path():
    """Return the absolute path to ffsubsync.py inside the AppImage."""
    # When frozen (inside an AppImage) PyInstaller defines sys._MEIPASS.
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, "ffsubsync", "ffsubsync.py")

def _run_ffsubsync(video_path, sub_path, offset):
    """Execute the bundled ffsubsync script and return its stdout."""
    script = _ffsubsync_path()
    if not os.path.isfile(script):
        raise FileNotFoundError(f"ffsubsync script not found at {script}")

    cmd = [
        sys.executable,               # the python interpreter that PyInstaller bundled
        script,
        "--video", video_path,
        "--sub",   sub_path,
        f"--offset={offset}"
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # ffsubsync writes diagnostics to stderr
        return e.stderr or ""

def _parse_offset(txt):
    """Convert user input to a float – empty string → 0.0."""
    try:
        return float(txt)
    except ValueError:
        return 0.0


# ----------------------------------------------------------------------
# Main Tkinter application
# ----------------------------------------------------------------------
class FFSubSyncGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        # Force a sane locale on systems that have only “C”
        os.environ.setdefault("LC_ALL", "C.UTF-8")

        self.title("FFSubSync – GUI")
        self.geometry("560x210")
        self.resizable(False, False)

        # ---------- Video row ----------
        video_fr = tk.LabelFrame(self, text="Video file")
        video_fr.pack(fill="x", padx=10, pady=5, ipady=5)

        tk.Label(video_fr, text="Path:").grid(row=0, column=0,
                                              sticky="e", padx=5, pady=2)
        self.video_path = tk.StringVar()
        e_video = tk.Entry(video_fr, textvariable=self.video_path, width=40)
        e_video.grid(row=0, column=1, sticky="we", padx=5, pady=2)
        btn_browse_v = tk.Button(video_fr, text="…", command=self.browse_video)
        btn_browse_v.grid(row=0, column=2, padx=5)

        # ---------- Subtitle row ----------
        sub_fr = tk.LabelFrame(self, text="Subtitle file")
        sub_fr.pack(fill="x", padx=10, pady=5, ipady=5)

        tk.Label(sub_fr, text="Path:").grid(row=0, column=0,
                                            sticky="e", padx=5, pady=2)
        self.sub_path = tk.StringVar()
        e_sub = tk.Entry(sub_fr, textvariable=self.sub_path, width=40)
        e_sub.grid(row=0, column=1, sticky="we", padx=5, pady=2)
        btn_browse_s = tk.Button(sub_fr, text="…", command=self.browse_sub)
        btn_browse_s.grid(row=0, column=2, padx=5)

        # ---------- Offset row ----------
        off_fr = tk.LabelFrame(self, text="Subtitle offset (seconds)")
        off_fr.pack(fill="x", padx=10, pady=5, ipady=5)

        tk.Label(off_fr, text="Delay:").grid(row=0, column=0,
                                             sticky="e", padx=5, pady=2)
        self.offset = tk.StringVar(value="0.0")
        e_off = tk.Entry(off_fr, textvariable=self.offset, width=10)
        e_off.grid(row=0, column=1, sticky="we", padx=5, pady=2)

        # ---------- Run button ----------
        self.run_btn = tk.Button(self, text="▶ Scan & Sync",
                                 command=self.run_sync,
                                 bg="#4caf50", fg="white", width=20)
        self.run_btn.pack(pady=15)

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def browse_video(self):
        p = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.flv *.webm")]
        )
        if p:
            self.video_path.set(p)

    def browse_sub(self):
        p = filedialog.askopenfilename(
            title="Select subtitle file",
            filetypes=[("Subtitles", "*.srt *.ass *.ttml *.vtt *.sub")]
        )
        if p:
            self.sub_path.set(p)

    # ------------------------------------------------------------------
    # Main action
    # ------------------------------------------------------------------
    def run_sync(self):
        video = self.video_path.get().strip()
        sub   = self.sub_path.get().strip()
        offset = _parse_offset(self.offset.get().strip())

        # ---- Basic validation ------------------------------------------------
        if not video or not os.path.isfile(video):
            messagebox.showwarning("Video missing", "Pick a valid video file.")
            return
        if not sub or not os.path.isfile(sub):
            messagebox.showwarning("Subtitle missing", "Pick a valid subtitle file.")
            return

        # ---- Execute the original ffsubsync script ---------------------------
        try:
            out = _run_ffsubsync(video, sub, offset)
            if out:
                messagebox.showinfo("FFSubSync finished", out.strip())
            else:
                messagebox.showinfo("FFSubSync finished",
                                    "No output – subtitles may already be in sync.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = FFSubSyncGUI()
    app.mainloop()

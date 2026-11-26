"""Cooperative focus for the managed desktop app. Never starts a new instance."""
import time
import tkinter as tk

def poll_focus(root,store):
    path=store/'focus-request.json'
    try:
        stamp=path.stat().st_mtime
        path.unlink()
    except OSError:
        return False
    if not -2<=time.time()-stamp<=15: return False  # tolerate filesystem/clock granularity
    try:
        root.deiconify(); root.lift(); root.focus_set()
    except tk.TclError:
        return False
    return True

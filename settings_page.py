import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    """Load settings from settings.json or return default values."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Settings file is corrupted.")
    return {"backup_folder": "backups", "max_backups": 5}

def save_settings(settings):
    """Save settings to settings.json."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def settings_page(root, settings, preselected_file=None):
    """Settings page with optional preselected file."""
    # Settings logic...

    frame = tk.Frame(root)

    # Title
    tk.Label(frame, text="Settings", font=("Arial", 16)).pack(pady=10)

    # Backup folder logic here...

    return frame
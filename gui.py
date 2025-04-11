import os
import sys
import json
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Import ttk for themed widgets
from gui_commit_page import commit_page
from restore_page import restore_page
from settings_page import settings_page

# Paths and constants
SETTINGS_FILE = "settings.json"
DEFAULT_BACKUP_FOLDER = "backups"


def load_settings():
    """Load settings from settings.json or return default values."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            print("Error: settings.json is corrupted. Resetting to default settings.")
    
    # Reset to default settings and save the file
    default_settings = {"backup_folder": DEFAULT_BACKUP_FOLDER, "max_backups": 5}
    save_settings(default_settings)
    return default_settings


def save_settings(settings):
    """Save settings to settings.json."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def main():
    # Check for a file path passed as an argument
    preselected_file = None
    if len(sys.argv) > 1:
        preselected_file = sys.argv[1]
        if not os.path.exists(preselected_file):
            messagebox.showerror("Error", f"The selected file does not exist: {preselected_file}")
            preselected_file = None

    # Load settings
    settings = load_settings()

    # Create the main Tkinter window
    root = tk.Tk()
    root.title("File Manager GUI")
    root.geometry("600x400")

    # Create a Notebook (tabbed interface)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Add pages to the Notebook
    notebook.add(commit_page(root, settings, preselected_file), text="Commit")
    notebook.add(restore_page(root, settings, preselected_file), text="Restore")
    notebook.add(settings_page(root, settings, preselected_file), text="Settings")

    # Start the Tkinter main loop
    root.mainloop()


if __name__ == "__main__":
    main()
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import hashlib
import json
import datetime

# File paths
TRACKED_FILES_PATH = "tracked_files.json"

def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as file:
            while chunk := file.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except FileNotFoundError:
        return None

def load_tracked_files():
    """Load tracked file metadata from JSON."""
    if not os.path.exists(TRACKED_FILES_PATH):
        return {}
    try:
        with open(TRACKED_FILES_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}

def save_tracked_files(tracked_files):
    """Save tracked file metadata to JSON."""
    with open(TRACKED_FILES_PATH, "w", encoding="utf-8") as file:
        json.dump(tracked_files, file, indent=4)

def get_backup_folder(settings):
    """Fetch the dynamic backup folder and ensure it exists."""
    backup_folder = settings.get("backup_folder", "backups")  # Default to "backups"
    try:
        os.makedirs(backup_folder, exist_ok=True)  # Ensure folder exists
    except OSError as e:
        raise Exception(f"Failed to create/access backup folder: {backup_folder}. Error: {e}")
    return backup_folder

def commit_page(root, settings, preselected_file=None):
    """Commit page with optional preselected file."""
    selected_file = preselected_file

    def select_file():
        """Open a file dialog to select a file and display its path."""
        nonlocal selected_file
        file_path = filedialog.askopenfilename()
        if file_path:
            selected_file = file_path
            selected_file_label.config(text=f"Selected File: {file_path}")
            commit_button.config(state=tk.NORMAL)
        else:
            selected_file = None
            selected_file_label.config(text="No file selected")
            commit_button.config(state=tk.DISABLED)

    def commit_file_action():
        """Handle the commit action."""
        if not selected_file:
            messagebox.showerror("Error", "No file selected! Please select a file to commit.")
            return

        commit_message = commit_message_entry.get().strip()
        username = os.getlogin()  # Current system user

        # Validate commit message
        if not commit_message:
            messagebox.showerror("Error", "Commit message cannot be empty!")
            return

        if len(commit_message) > 200:
            messagebox.showerror("Error", "Commit message too long! Max 200 characters.")
            return

        # Load tracked files and check for changes
        tracked_files = load_tracked_files()
        current_hash = calculate_file_hash(selected_file)

        # Ensure the file is in the tracked files structure
        if selected_file not in tracked_files:
            tracked_files[selected_file] = {"versions": {}}

        # Get the file's version history
        file_versions = tracked_files[selected_file]["versions"]

        # Check if the current hash already exists
        if current_hash in file_versions:
            messagebox.showinfo("No Changes Detected", f"No changes detected for {selected_file}. Commit skipped.")
            return

        # Get backup folder and create a backup file
        backup_folder = get_backup_folder(settings)
        backup_file_path = os.path.join(backup_folder, current_hash)
        try:
            shutil.copy(selected_file, backup_file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create a backup file: {str(e)}")
            return

        # Save the new version metadata
        file_versions[current_hash] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "username": username,
            "commit_message": commit_message
        }
        save_tracked_files(tracked_files)

        messagebox.showinfo("Success", f"File '{selected_file}' committed successfully!")

    frame = tk.Frame(root)

    # Title
    tk.Label(frame, text="Commit", font=("Arial", 16)).pack(pady=10)

    # Selected file
    selected_file_label = tk.Label(frame, text="No file selected", font=("Arial", 10), fg="gray")
    selected_file_label.pack(pady=5)
    tk.Button(frame, text="Select File", command=select_file).pack(pady=5)

    # Commit message
    tk.Label(frame, text="Commit Message:", font=("Arial", 12)).pack(pady=5)
    commit_message_entry = tk.Entry(frame, width=50)
    commit_message_entry.pack(pady=5)

    # Commit button
    commit_button = tk.Button(frame, text="Commit", command=commit_file_action, state=tk.DISABLED)
    commit_button.pack(pady=10)

    return frame

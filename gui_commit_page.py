import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import hashlib
import json
import datetime

# File paths
TRACKED_FILES_PATH = "tracked_files.json"
BACKUP_FOLDER = r"C:\Project\inveni\inveni\backups"  # Default backup folder

# Ensure the backup folder exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)

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

        # Create a backup file in the BACKUP_FOLDER with the file's hash as its name
        backup_file_path = os.path.join(BACKUP_FOLDER, current_hash)
        try:
            shutil.copy(selected_file, backup_file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create a backup file: {str(e)}")
            return

        # Update tracked files with the new hash and metadata
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_versions[current_hash] = {
            "timestamp": timestamp,
            "commit_message": commit_message,
            "username": username,
        }
        save_tracked_files(tracked_files)

        # Show success message
        messagebox.showinfo("Success", f"File committed successfully!\n\nFile: {selected_file}\nUser: {username}")
        selected_file_label.config(text="No file selected")
        commit_message_entry.delete(0, tk.END)

    frame = tk.Frame(root)

    # Title
    tk.Label(frame, text="Commit a File", font=("Arial", 16)).pack(pady=10)

    # File selection
    selected_file_label = tk.Label(frame, text=f"Selected File: {selected_file}" if selected_file else "No file selected", font=("Arial", 10), fg="gray")
    selected_file_label.pack(pady=5)
    tk.Button(frame, text="Select File", command=select_file).pack(pady=5)

    # Commit message
    tk.Label(frame, text="Commit Message:").pack(pady=5)
    commit_message_entry = tk.Entry(frame, width=50)
    commit_message_entry.pack(pady=5)

    # Commit button
    commit_button = tk.Button(frame, text="Commit", command=commit_file_action)
    commit_button.pack(pady=10)

    # Enable or disable the commit button based on whether a file is preselected
    if selected_file:
        commit_button.config(state=tk.NORMAL)
    else:
        commit_button.config(state=tk.DISABLED)

    return frame
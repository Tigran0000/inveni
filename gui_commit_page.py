import os
import shutil
import gzip
import tkinter as tk
from tkinter import filedialog, messagebox
import hashlib
import datetime
from utils import load_tracked_files, save_tracked_files


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


def enforce_max_backups(file_backup_dir, max_backups):
    """Enforce the maximum number of backups allowed for a specific file."""
    backups = sorted(
        os.listdir(file_backup_dir),
        key=lambda x: os.path.getctime(os.path.join(file_backup_dir, x))
    )
    while len(backups) > max_backups:
        oldest_backup = backups.pop(0)  # Remove the oldest backup
        oldest_backup_path = os.path.join(file_backup_dir, oldest_backup)
        os.remove(oldest_backup_path)
        print(f"Deleted old backup: {oldest_backup_path}")


def commit_page(root, settings, shared_state):
    """Commit page with SharedState integration."""
    backup_folder = settings.get("backup_folder", "backups")
    os.makedirs(backup_folder, exist_ok=True)

    selected_file = shared_state.get_selected_file()

    def select_file():
        """Open a file dialog to select a file and update the shared state."""
        file_path = filedialog.askopenfilename()
        if file_path:
            shared_state.set_selected_file(file_path)
        else:
            shared_state.set_selected_file(None)

    def on_file_updated(file_path):
        """Callback to update the UI when the selected file changes."""
        nonlocal selected_file
        selected_file = file_path
        if selected_file:
            selected_file_label.config(text=f"Selected File: {selected_file}")
            commit_button.config(state=tk.NORMAL)
            commit_message_entry.config(state=tk.NORMAL)
        else:
            selected_file_label.config(text="No file selected")
            commit_button.config(state=tk.DISABLED)
            commit_message_entry.config(state=tk.DISABLED)

    def commit_file_action():
        """Handle the commit action."""
        nonlocal selected_file
        selected_file = shared_state.get_selected_file()

        # Check if a file is selected
        if not selected_file:
            messagebox.showerror("Error", "No file selected! Please select a file to commit.")
            return

        # Normalize the file path
        normalized_file_path = os.path.normpath(selected_file)

        # Ensure the file exists
        if not os.path.exists(normalized_file_path):
            messagebox.showerror("Error", f"Selected file does not exist: {selected_file}")
            return

        commit_message = commit_message_entry.get().strip()
        username = os.getlogin()

        # Validate commit message
        if not commit_message:
            messagebox.showerror("Error", "Commit message cannot be empty!")
            return

        if len(commit_message) > 200:
            messagebox.showerror("Error", "Commit message too long! Max 200 characters.")
            return

        # Load and update tracked files
        tracked_files = load_tracked_files()
        current_hash = calculate_file_hash(normalized_file_path)

        if current_hash is None:
            messagebox.showerror("Error", f"Failed to calculate file hash for: {normalized_file_path}")
            return

        if normalized_file_path not in tracked_files:
            tracked_files[normalized_file_path] = {"versions": {}}

        file_versions = tracked_files[normalized_file_path]["versions"]

        if current_hash in file_versions:
            messagebox.showinfo("No Changes Detected", f"No changes detected for {normalized_file_path}. Commit skipped.")
            return

        # Create a subdirectory for this file's backups
        file_backup_dir = os.path.join(backup_folder, os.path.basename(normalized_file_path))
        os.makedirs(file_backup_dir, exist_ok=True)

        # Create a timestamped backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file_path = os.path.join(file_backup_dir, f"backup_{timestamp}.gz")
        try:
            with open(normalized_file_path, "rb") as src, gzip.open(backup_file_path, "wb") as dest:
                shutil.copyfileobj(src, dest)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create a backup file: {str(e)}")
            return

        # Enforce backup quota for this file
        enforce_max_backups(file_backup_dir, settings["max_backups"])

        # Save the new version
        commit_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_versions[current_hash] = {
            "timestamp": commit_timestamp,
            "commit_message": commit_message,
            "username": username,
        }
        save_tracked_files(tracked_files)

        # Notify shared state
        shared_state.set_selected_file(selected_file)

        messagebox.showinfo("Success", f"File committed successfully!\n\nFile: {normalized_file_path}\nUser: {username}")

    frame = tk.Frame(root)

    # Title
    tk.Label(frame, text="Commit a File", font=("Arial", 16)).pack(pady=10)

    # File selection
    selected_file_label = tk.Label(
        frame,
        text=f"Selected File: {selected_file}" if selected_file else "No file selected",
        font=("Arial", 10),
        fg="gray",
    )
    selected_file_label.pack(pady=5)
    tk.Button(frame, text="Select File", command=select_file).pack(pady=5)

    # Commit message
    tk.Label(frame, text="Commit Message:").pack(pady=5)
    commit_message_entry = tk.Entry(frame, width=50, state=tk.DISABLED)
    commit_message_entry.pack(pady=5)

    # Commit button
    commit_button = tk.Button(frame, text="Commit", command=commit_file_action, state=tk.DISABLED)
    commit_button.pack(pady=10)

    # Register the callback
    shared_state.add_callback(on_file_updated)

    return frame

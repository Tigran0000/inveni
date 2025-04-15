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


def enforce_max_backups_per_file(file_backup_folder, max_backups):
    """
    Enforce the maximum number of backups allowed in the folder
    specific to a file.
    """
    backups = sorted(
        os.listdir(file_backup_folder),
        key=lambda x: os.path.getctime(os.path.join(file_backup_folder, x))
    )
    while len(backups) > max_backups:
        oldest_backup = backups.pop(0)  # Remove the oldest backup
        oldest_backup_path = os.path.join(file_backup_folder, oldest_backup)
        os.remove(oldest_backup_path)
        print(f"Deleted old backup: {oldest_backup_path}")


def commit_page(root, settings, shared_state):
    """Commit page with SharedState integration."""
    backup_folder = settings.get("backup_folder", "backups")
    os.makedirs(backup_folder, exist_ok=True)

    # Define `selected_file` in the enclosing scope
    selected_file = shared_state.get_selected_file()

    def select_file():
        """Open a file dialog to select a file and update the shared state."""
        nonlocal selected_file  # Reference the variable from the enclosing scope
        file_path = filedialog.askopenfilename()
        if file_path:
            shared_state.set_selected_file(file_path)
            selected_file = file_path
        else:
            shared_state.set_selected_file(None)
            selected_file = None

    def get_last_commit():
        """Retrieve the last commit details for the selected file."""
        if not selected_file:
            return "No file selected", ""

        tracked_files = load_tracked_files()
        normalized_file_path = os.path.normpath(selected_file)

        if normalized_file_path not in tracked_files:
            return "No commits available", ""

        file_versions = tracked_files[normalized_file_path]["versions"]
        if not file_versions:
            return "No commits available", ""

        # Get the most recent commit
        last_commit_hash = max(file_versions, key=lambda k: file_versions[k]["timestamp"])
        last_commit = file_versions[last_commit_hash]
        return last_commit["commit_message"], last_commit["timestamp"]

    def refresh_last_commit():
        """Refresh the last commit information."""
        commit_message, commit_time = get_last_commit()
        last_commit_label.config(text=f"Last Commit: {commit_time or 'N/A'} - {commit_message or 'No message'}")

    def on_file_updated(file_path):
        """Callback to update the UI when the selected file changes."""
        nonlocal selected_file  # Reference the variable from the enclosing scope
        selected_file = file_path
        if selected_file:
            selected_file_label.config(text=f"Selected File: {selected_file}")
            commit_button.config(state=tk.NORMAL)
            commit_message_entry.config(state=tk.NORMAL)
        else:
            selected_file_label.config(text="No file selected")
            commit_button.config(state=tk.DISABLED)
            commit_message_entry.config(state=tk.DISABLED)

        # Refresh the last commit details when the file is updated
        refresh_last_commit()

    def commit_file_action(event=None):
        """Handle the commit action."""
        nonlocal selected_file  # Reference the variable from the enclosing scope
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

        # Create a file-specific backup folder
        base_file_name = os.path.basename(normalized_file_path)
        file_backup_folder = os.path.join(backup_folder, base_file_name)

        # DEBUG: Log the folder path
        print(f"DEBUG: Backup folder: {file_backup_folder}")

        os.makedirs(file_backup_folder, exist_ok=True)

        # Create a hash-based backup file path
        backup_file_path = os.path.join(file_backup_folder, f"{base_file_name}_{current_hash}.gz")

        # DEBUG: Log the final backup file path
        print(f"DEBUG: Backup file path: {backup_file_path}")

        try:
            with open(normalized_file_path, "rb") as src, gzip.open(backup_file_path, "wb") as dest:
                shutil.copyfileobj(src, dest)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create a backup file: {str(e)}")
            return

        # Enforce backup quota for this specific file
        enforce_max_backups_per_file(file_backup_folder, settings["max_backups"])

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

        # Refresh the last commit details after a new commit
        refresh_last_commit()

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

    # Last commit section
    last_commit_label = tk.Label(frame, text="Last Commit: No file selected", font=("Arial", 10), fg="blue")
    last_commit_label.pack(pady=5)

    # Commit message
    tk.Label(frame, text="Commit Message:").pack(pady=5)
    commit_message_entry = tk.Entry(frame, width=50, state=tk.DISABLED)
    commit_message_entry.pack(pady=5)

    # Bind Enter key to the commit action
    commit_message_entry.bind("<Return>", commit_file_action)

    # Commit button
    commit_button = tk.Button(frame, text="Commit", command=commit_file_action, state=tk.DISABLED)
    commit_button.pack(pady=10)

    # Register the callback
    shared_state.add_callback(on_file_updated)

    return frame

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json

TRACKED_FILES_PATH = "tracked_files.json"
BACKUP_FOLDER = r"C:\Project\inveni\inveni\backups"  # Updated default backup folder

# Ensure the backup folder exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)

def load_tracked_files():
    """Load tracked file metadata from JSON."""
    if not os.path.exists(TRACKED_FILES_PATH):
        return {}
    try:
        with open(TRACKED_FILES_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}

def restore_version(file_path, version_hash):
    """Restore the file to the specified version."""
    backup_file_path = os.path.join(BACKUP_FOLDER, version_hash)

    if not os.path.exists(backup_file_path):
        raise FileNotFoundError(f"Backup file for version {version_hash} not found.")
    
    try:
        shutil.copy(backup_file_path, file_path)
    except Exception as e:
        raise Exception(f"Failed to restore the file: {str(e)}")

def restore_page(root, settings, preselected_file=None):
    selected_file = preselected_file
    tracked_files = load_tracked_files()

    def update_version_list():
        """Update the version list based on the selected file."""
        version_list.delete(*version_list.get_children())  # Clear existing entries

        if not selected_file or selected_file not in tracked_files:
            messagebox.showwarning("Warning", "No tracked versions found for the selected file.")
            return

        # Retrieve the metadata for the selected file
        file_metadata = tracked_files[selected_file]

        # Ensure the file has a "versions" key
        if "versions" not in file_metadata:
            messagebox.showwarning("Warning", "No version history found for the selected file.")
            return

        # Populate the version list with metadata
        for version_hash, metadata in file_metadata["versions"].items():
            version_list.insert(
                "", "end", values=(
                    metadata.get("timestamp", "Unknown"),
                    metadata.get("username", "Unknown"),
                    metadata.get("commit_message", "No message"),
                    version_hash,
                )
            )

    def select_file():
        """Open a file dialog to select a file and update the version list."""
        nonlocal selected_file
        file_path = filedialog.askopenfilename()
        if file_path:
            selected_file = file_path
            selected_file_label.config(text=f"Selected File: {file_path}")
            update_version_list()

    def restore_selected_version():
        """Restore the selected version of the file."""
        selected_item = version_list.selection()

        if not selected_file:
            messagebox.showerror("Error", "No file selected! Please select a file to restore.")
            return

        if not selected_item:
            messagebox.showerror("Error", "No version selected! Please select a version to restore.")
            return

        # Get the version hash from the selected item
        version_hash = version_list.item(selected_item, "values")[3]

        try:
            restore_version(selected_file, version_hash)
            messagebox.showinfo("Success", f"File '{selected_file}' has been restored to the selected version.")
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore the file: {str(e)}")

    frame = tk.Frame(root)

    # Title
    tk.Label(frame, text="Restore a File", font=("Arial", 16)).pack(pady=10)

    # Selected file label
    selected_file_label = tk.Label(frame, text=f"Selected File: {selected_file}" if selected_file else "No file selected", font=("Arial", 10), fg="gray")
    selected_file_label.pack(pady=5)

    # Select file button
    tk.Button(frame, text="Select File", command=select_file).pack(pady=5)

    # Version list
    tk.Label(frame, text="Select a Version:").pack(pady=5)
    version_list = ttk.Treeview(frame, columns=("Timestamp", "User", "Message", "Hash"), show="headings", height=8)
    version_list.pack(pady=5, fill="x", expand=True)

    # Define the columns
    version_list.heading("Timestamp", text="Date and Time")
    version_list.heading("User", text="User")
    version_list.heading("Message", text="Commit Message")
    version_list.heading("Hash", text="Version Hash")
    version_list.column("Hash", width=250)  # Adjust width for better visibility

    # Restore button
    tk.Button(frame, text="Restore Selected Version", command=restore_selected_version).pack(pady=10)

    # Automatically update the version list if a file is preselected
    if selected_file:
        update_version_list()

    return frame
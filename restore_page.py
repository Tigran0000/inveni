import os
import shutil
import gzip
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from utils import load_tracked_files

def decompress_file(compressed_file_path, output_file_path):
    """Decompress a gzip file."""
    try:
        with gzip.open(compressed_file_path, "rb") as f_in:
            with open(output_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        raise Exception(f"Decompression failed: {str(e)}")

def restore_version(file_path, version_hash, backup_folder):
    """Restore the file to the specified version."""
    compressed_backup_file_path = os.path.join(backup_folder, f"{version_hash}.gz")

    if not os.path.exists(compressed_backup_file_path):
        raise FileNotFoundError(f"Backup file for version {version_hash} not found.")

    try:
        decompress_file(compressed_backup_file_path, file_path)
    except Exception as e:
        raise Exception(f"Failed to restore the file: {str(e)}")

def restore_page(root, settings, shared_state):
    """Restore page GUI for restoring file versions."""
    selected_file = shared_state.get_selected_file()
    backup_folder = settings.get("backup_folder", "backups")
    os.makedirs(backup_folder, exist_ok=True)

    def update_version_list():
        """Update the version list based on the selected file."""
        version_list.delete(*version_list.get_children())

        if not selected_file:
            return

        tracked_files = load_tracked_files()
        normalized_file_path = os.path.normpath(selected_file)

        if normalized_file_path not in tracked_files:
            return

        file_metadata = tracked_files[normalized_file_path]
        if "versions" not in file_metadata or not file_metadata["versions"]:
            return

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
            update_version_list()
        else:
            selected_file_label.config(text="No file selected")
            version_list.delete(*version_list.get_children())

    def restore_selected_version():
        """Restore the selected version of the file."""
        selected_item = version_list.selection()
        if not selected_file or not selected_item:
            messagebox.showerror("Error", "No file or version selected!")
            return

        version_hash = version_list.item(selected_item, "values")[3]
        try:
            restore_version(selected_file, version_hash, backup_folder)
            messagebox.showinfo("Success", f"File '{selected_file}' has been restored to the selected version.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore the file: {str(e)}")

    frame = tk.Frame(root)
    tk.Label(frame, text="Restore a File", font=("Arial", 16)).pack(pady=10)

    selected_file_label = tk.Label(
        frame,
        text=f"Selected File: {selected_file}" if selected_file else "No file selected",
        font=("Arial", 10),
        fg="gray"
    )
    selected_file_label.pack(pady=5)
    tk.Button(frame, text="Select File", command=select_file).pack(pady=5)

    tk.Label(frame, text="Select a Version:").pack(pady=5)
    version_list = ttk.Treeview(frame, columns=("Timestamp", "User", "Message", "Hash"), show="headings", height=8)
    version_list.pack(pady=5, fill="x", expand=True)
    version_list.heading("Timestamp", text="Date and Time")
    version_list.heading("User", text="User")
    version_list.heading("Message", text="Commit Message")
    version_list.heading("Hash", text="Version Hash")
    version_list.column("Hash", width=250)

    tk.Button(frame, text="Restore Selected Version", command=restore_selected_version).pack(pady=10)

    shared_state.add_callback(on_file_updated)

    return frame

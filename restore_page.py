import os
import tkinter as tk
from tkinter import messagebox, ttk
from utils import load_tracked_files, restore_file_version


def restore_page(root: tk.Tk, settings: dict, shared_state) -> tk.Frame:
    """Restore Page: Allows users to restore file versions."""
    backup_folder = settings.get("backup_folder", "backups")
    selected_file = shared_state.get_selected_file()

    def refresh_version_list():
        """Refresh the version list for the selected file."""
        version_tree.delete(*version_tree.get_children())  # Clear existing entries

        if not selected_file:
            version_tree.insert("", "end", values=("No file selected", "", ""))
            return

        tracked_files = load_tracked_files()
        normalized_file_path = os.path.normpath(selected_file)

        if normalized_file_path not in tracked_files:
            version_tree.insert("", "end", values=("No versions available", "", ""))
            return

        file_versions = tracked_files[normalized_file_path]["versions"]

        # Sort versions by timestamp (newest first)
        sorted_versions = sorted(
            file_versions.items(),
            key=lambda item: item[1]["timestamp"],
            reverse=True
        )

        for version_hash, metadata in sorted_versions:
            # Add only timestamp, commit message, and username to the tree
            version_tree.insert(
                "",
                "end",
                values=(
                    metadata.get("timestamp", "Unknown"),
                    metadata.get("commit_message", "No message"),
                    metadata.get("username", "Unknown"),
                ),
                tags=(version_hash,),  # Store the hash in the item's tag for internal use
            )

    def restore_selected_version():
        """Restore the selected version of the file."""
        selected_item = version_tree.focus()  # Get the currently selected item
        if not selected_item:
            messagebox.showerror("Error", "No version selected! Please select a version to restore.")
            return

        # Retrieve the hash stored in the item's tag
        selected_hash = version_tree.item(selected_item, "tags")[0]
        if not selected_hash:
            messagebox.showerror("Error", "Failed to retrieve the version hash.")
            return

        # Retrieve additional information for debugging (not displayed in UI)
        values = version_tree.item(selected_item, "values")
        selected_timestamp, selected_message, selected_username = values

        # Create the file-specific backup folder path
        base_file_name = os.path.basename(selected_file)
        file_backup_folder = os.path.join(backup_folder, base_file_name)

        try:
            restore_file_version(selected_file, selected_hash, file_backup_folder)
            messagebox.showinfo(
                "Success",
                f"File restored to version from: {selected_timestamp}\nCommit Message: {selected_message}\nUser: {selected_username}"
            )
        except FileNotFoundError:
            messagebox.showerror("Error", f"Backup file not found for the selected version.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore the file version: {str(e)}")

    def on_file_updated(file_path: str):
        """Callback to update the UI when the selected file changes."""
        nonlocal selected_file
        selected_file = file_path
        if selected_file:
            selected_file_label.config(text=f"Selected File: {selected_file}")
            restore_button.config(state=tk.NORMAL)
        else:
            selected_file_label.config(text="No file selected")
            restore_button.config(state=tk.DISABLED)

        # Refresh the version list whenever the file is updated
        refresh_version_list()

    # UI Setup
    frame = tk.Frame(root)

    # Title
    tk.Label(frame, text="Restore a File", font=("Arial", 16)).pack(pady=10)

    # File selection info
    selected_file_label = tk.Label(
        frame,
        text=f"Selected File: {selected_file}" if selected_file else "No file selected",
        font=("Arial", 10),
        fg="gray",
    )
    selected_file_label.pack(pady=5)

    # Version list
    version_tree = ttk.Treeview(frame, columns=("Timestamp", "Message", "User"), show="headings", height=8)
    version_tree.pack(pady=10, fill="x", expand=True)
    version_tree.heading("Timestamp", text="Date and Time")
    version_tree.heading("Message", text="Commit Message")
    version_tree.heading("User", text="User")

    # Restore button
    restore_button = tk.Button(frame, text="Restore Selected Version", command=restore_selected_version, state=tk.DISABLED)
    restore_button.pack(pady=10)

    # Register the callback
    shared_state.add_callback(on_file_updated)

    return frame

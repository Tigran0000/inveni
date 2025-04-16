import os
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import pytz
from utils import (
    load_tracked_files, 
    restore_file_version, 
    format_size, 
    get_file_metadata
)
from time_utils import get_current_times, format_timestamp_dual


def restore_page(root: tk.Tk, settings: dict, shared_state) -> tk.Frame:
    """Restore Page with improved time handling and dynamic username."""
    backup_folder = settings.get("backup_folder", "backups")
    selected_file = shared_state.get_selected_file()
    username = os.getlogin()  # Get current Windows username

    def update_time_display():
        """Update the current time display."""
        times = get_current_times()
        current_time_label.config(
            text=(f"Current Time (UTC): {times['utc']}\n"
                  f"Local Time: {times['local']}\n"
                  f"Current User: {username}")
        )
        frame.after(1000, update_time_display)

    def refresh_version_list():
        """Refresh the version list with time information."""
        version_tree.delete(*version_tree.get_children())

        if not selected_file or not os.path.exists(selected_file):
            version_tree.insert("", "end", values=("No file selected", "", "", "", "", "", ""))
            return

        tracked_files = load_tracked_files()
        normalized_path = os.path.normpath(selected_file)
        
        if normalized_path not in tracked_files:
            version_tree.insert("", "end", values=("No versions available", "", "", "", "", "", ""))
            return

        versions = tracked_files[normalized_path]["versions"]
        
        # Sort versions by timestamp (newest first)
        sorted_versions = sorted(
            versions.items(),
            key=lambda x: datetime.strptime(x[1]["timestamp"], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )

        for version_hash, info in sorted_versions:
            metadata = info.get("metadata", {})
            utc_time, local_time = format_timestamp_dual(info["timestamp"])
            
            version_tree.insert(
                "",
                "end",
                values=(
                    utc_time,
                    local_time,
                    info["commit_message"],
                    info.get("username", username),
                    format_size(metadata.get("size", 0)),
                    metadata.get("modification_time", {}).get("local", "Unknown"),
                    metadata.get("file_type", "unknown")
                ),
                tags=(version_hash,)
            )

        # Update current file metadata
        update_current_metadata()

    def update_current_metadata():
        """Update the current file metadata display."""
        if not selected_file or not os.path.exists(selected_file):
            current_metadata_label.config(text="Current File: No file selected")
            return

        try:
            metadata = get_file_metadata(selected_file)
            current_metadata_label.config(
                text=(f"Current File: {os.path.basename(selected_file)}\n"
                      f"Size: {format_size(metadata['size'])}\n"
                      f"Modified: {metadata['modification_time']['local']}\n"
                      f"Type: {metadata['file_type']}")
            )
        except Exception as e:
            current_metadata_label.config(text=f"Error getting metadata: {str(e)}")

    def restore_selected_version():
        """Restore a selected version with time information."""
        if not selected_file or not version_tree.selection():
            messagebox.showerror("Error", "Please select a version to restore.")
            return

        selected_item = version_tree.selection()[0]
        version_hash = version_tree.item(selected_item)["tags"][0]
        values = version_tree.item(selected_item)["values"]
        
        utc_time, local_time, message, user, size, modified, file_type = values

        if messagebox.askyesno(
            "Confirm Restore",
            f"Restore this version?\n\n"
            f"UTC Time: {utc_time}\n"
            f"Local Time: {local_time}\n"
            f"Message: {message}\n"
            f"Size: {size}\n"
            f"Modified: {modified}\n"
            f"Type: {file_type}\n"
            f"Created by: {user}"
        ):
            try:
                restore_file_version(selected_file, version_hash, backup_folder)
                
                times = get_current_times()
                messagebox.showinfo(
                    "Success",
                    f"File restored successfully!\n\n"
                    f"Restored version from: {local_time}\n"
                    f"Current time (UTC): {times['utc']}\n"
                    f"Current time (Local): {times['local']}"
                )
                
                refresh_version_list()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore: {str(e)}")

    # UI Setup
    frame = tk.Frame(root)

    # Title and time display
    tk.Label(frame, text="Restore Version", font=("Arial", 16, "bold")).pack(pady=10)
    current_time_label = tk.Label(frame, text="", font=("Arial", 10))
    current_time_label.pack(pady=5)

    # Current file metadata
    current_metadata_label = tk.Label(
        frame,
        text="Current File: No file selected",
        font=("Arial", 10),
        justify=tk.LEFT
    )
    current_metadata_label.pack(pady=5, anchor="w", padx=10)

    # Version list
    tree_frame = tk.Frame(frame)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # Scrollbars
    y_scroll = ttk.Scrollbar(tree_frame)
    y_scroll.pack(side="right", fill="y")
    
    x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
    x_scroll.pack(side="bottom", fill="x")

    # Treeview
    version_tree = ttk.Treeview(
        tree_frame,
        columns=(
            "UTC Time",
            "Local Time",
            "Message",
            "User",
            "Size",
            "Modified",
            "Type"
        ),
        show="headings",
        height=10,
        yscrollcommand=y_scroll.set,
        xscrollcommand=x_scroll.set
    )

    # Configure scrollbars
    y_scroll.config(command=version_tree.yview)
    x_scroll.config(command=version_tree.xview)

    # Configure columns
    version_tree.heading("UTC Time", text="UTC Time")
    version_tree.heading("Local Time", text="Local Time")
    version_tree.heading("Message", text="Message")
    version_tree.heading("User", text="User")
    version_tree.heading("Size", text="Size")
    version_tree.heading("Modified", text="Modified")
    version_tree.heading("Type", text="Type")

    version_tree.column("UTC Time", width=150, minwidth=150)
    version_tree.column("Local Time", width=150, minwidth=150)
    version_tree.column("Message", width=200, minwidth=200)
    version_tree.column("User", width=100, minwidth=100)
    version_tree.column("Size", width=100, minwidth=100)
    version_tree.column("Modified", width=150, minwidth=150)
    version_tree.column("Type", width=80, minwidth=80)

    version_tree.pack(side="left", fill="both", expand=True)

    # Restore button
    restore_button = tk.Button(
        frame,
        text="Restore Selected Version",
        command=restore_selected_version,
        state=tk.DISABLED
    )
    restore_button.pack(pady=10)

    # Register callbacks
    def on_file_updated(file_path):
        """Callback when file selection changes."""
        nonlocal selected_file
        selected_file = file_path
        
        if selected_file and os.path.exists(selected_file):
            restore_button.config(state=tk.NORMAL)
        else:
            restore_button.config(state=tk.DISABLED)
        
        refresh_version_list()

    shared_state.add_file_callback(on_file_updated)
    shared_state.add_version_callback(refresh_version_list)

    # Start time updates
    update_time_display()
    
    # Initial refresh
    refresh_version_list()

    return frame

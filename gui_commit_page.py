import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import pytz
from time_utils import get_current_times
from utils import (
    load_tracked_files,
    save_tracked_files,
    get_backup_path,
    create_backup,
    get_file_metadata,
    format_size,
    get_backup_count,
    has_file_changed,
    calculate_file_hash
)
from file_monitor import FileMonitor


def commit_page(root, settings, shared_state):
    """Commit page with improved change detection."""
    backup_folder = settings.get("backup_folder", "backups")
    os.makedirs(backup_folder, exist_ok=True)
    
    class State:
        def __init__(self):
            self.selected_file = shared_state.get_selected_file()
            self.has_changes = False
    
    state = State()
    username = os.getlogin()

    def on_file_changed(file_path: str, has_changes: bool) -> None:
        """Handle file change detection."""
        state.has_changes = has_changes
        update_metadata_display()

    # Initialize file monitor
    file_monitor = FileMonitor(on_file_changed)

    def check_file_changes():
        """Periodically check for file changes."""
        file_monitor.check_for_changes()
        frame.after(1000, check_file_changes)  # Check every second

    def update_time_display():
        """Update the current time display."""
        times = get_current_times()
        current_time_label.config(
            text=(f"Current Time (UTC): {times['utc']}\n"
                  f"Local Time: {times['local']}\n"
                  f"User: {username}")
        )
        frame.after(1000, update_time_display)

    def select_file():
        """Open file dialog to select a file."""
        file_path = filedialog.askopenfilename()
        if file_path:
            shared_state.set_selected_file(file_path)
            file_monitor.set_file(file_path)
        else:
            shared_state.set_selected_file(None)
            file_monitor.set_file(None)

    def update_metadata_display():
        """Update the metadata display with change status."""
        if not state.selected_file or not os.path.exists(state.selected_file):
            metadata_text.config(state=tk.NORMAL)
            metadata_text.delete(1.0, tk.END)
            metadata_text.insert(tk.END, "No file selected")
            metadata_text.config(state=tk.DISABLED)
            return

        try:
            metadata = get_file_metadata(state.selected_file)
            current_backups = get_backup_count(state.selected_file, backup_folder)
            max_backups = settings.get('max_backups', 5)
            
            change_status = "Modified" if state.has_changes else "No changes"
            status_color = "red" if state.has_changes else "green"
            
            info_text = (
                f"File: {os.path.basename(state.selected_file)}\n"
                f"Status: {change_status}\n"
                f"Size: {format_size(metadata['size'])}\n"
                f"Modified (UTC): {metadata['modification_time']['utc']}\n"
                f"Modified (Local): {metadata['modification_time']['local']}\n"
                f"Type: {metadata['file_type']}\n"
                f"Backups: {current_backups}/{max_backups}\n"
                f"Last Updated by: {metadata['username']}"
            )
            
            metadata_text.config(state=tk.NORMAL)
            metadata_text.delete(1.0, tk.END)
            metadata_text.insert(tk.END, info_text)
            
            # Change color of status line
            start_idx = info_text.find("Status: ")
            end_idx = info_text.find("\n", start_idx)
            if start_idx != -1 and end_idx != -1:
                metadata_text.tag_add("status", f"1.{start_idx}", f"1.{end_idx}")
                metadata_text.tag_config("status", foreground=status_color)
            
            metadata_text.config(state=tk.DISABLED)
            
        except Exception as e:
            metadata_text.config(state=tk.NORMAL)
            metadata_text.delete(1.0, tk.END)
            metadata_text.insert(tk.END, f"Error: {str(e)}")
            metadata_text.config(state=tk.DISABLED)

    def commit_file_action(event=None):
        """Handle the commit action with change detection."""
        if not state.selected_file or not os.path.exists(state.selected_file):
            messagebox.showerror("Error", "No valid file selected!")
            return

        commit_message = commit_message_entry.get().strip()
        if not commit_message:
            messagebox.showerror("Error", "Please enter a commit message!")
            return

        try:
            tracked_files = load_tracked_files()
            has_changed, current_hash, last_hash = has_file_changed(
                state.selected_file, 
                tracked_files
            )
            
            if not has_changed:
                response = messagebox.askyesno(
                    "No Changes", 
                    "No changes detected since last backup.\nDo you want to create a backup anyway?"
                )
                if not response:
                    return

            backup_path = create_backup(
                state.selected_file, 
                current_hash, 
                backup_folder, 
                settings
            )
            
            metadata = get_file_metadata(state.selected_file)
            times = get_current_times()
            
            normalized_path = os.path.normpath(state.selected_file)
            
            if normalized_path not in tracked_files:
                tracked_files[normalized_path] = {"versions": {}}

            tracked_files[normalized_path]["versions"][current_hash] = {
                "timestamp": times['utc'],
                "commit_message": commit_message,
                "username": username,
                "metadata": metadata,
                "previous_hash": last_hash
            }
            
            save_tracked_files(tracked_files)
            
            commit_message_entry.delete(0, tk.END)
            shared_state.notify_version_change()
            
            new_backup_count = get_backup_count(state.selected_file, backup_folder)
            change_type = "Modified" if has_changed else "No changes (manual backup)"
            
            messagebox.showinfo(
                "Success", 
                f"File committed successfully!\n\n"
                f"UTC Time: {times['utc']}\n"
                f"Local Time: {times['local']}\n"
                f"File: {os.path.basename(normalized_path)}\n"
                f"Size: {format_size(metadata['size'])}\n"
                f"Backups: {new_backup_count}/{settings.get('max_backups', 5)}\n"
                f"Status: {change_type}\n"
                f"User: {username}"
            )
            
            update_metadata_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to commit: {str(e)}")

    # UI Setup
    frame = tk.Frame(root)
    
    # Title
    tk.Label(frame, text="Commit Changes", font=("Arial", 16, "bold")).pack(pady=10)
    
    # Current time display
    current_time_label = tk.Label(frame, text="", font=("Arial", 10))
    current_time_label.pack(pady=5)
    
    # File selection
    file_frame = tk.LabelFrame(frame, text="File Selection", padx=5, pady=5)
    file_frame.pack(fill="x", padx=10, pady=5)
    
    tk.Button(file_frame, text="Select File", command=select_file).pack(pady=5)
    
    # Metadata display
    metadata_frame = tk.LabelFrame(frame, text="File Information", padx=5, pady=5)
    metadata_frame.pack(fill="x", padx=10, pady=5)
    
    metadata_text = tk.Text(metadata_frame, height=8, width=50, state=tk.DISABLED)
    metadata_text.pack(fill="x", padx=5, pady=5)
    
    # Commit section
    commit_frame = tk.LabelFrame(frame, text="Commit", padx=5, pady=5)
    commit_frame.pack(fill="x", padx=10, pady=5)
    
    tk.Label(commit_frame, text="Commit Message:").pack(pady=2)
    commit_message_entry = tk.Entry(commit_frame, width=50)
    commit_message_entry.pack(pady=5)
    commit_message_entry.bind("<Return>", commit_file_action)
    
    commit_button = tk.Button(
        commit_frame,
        text="Commit Changes",
        command=commit_file_action
    )
    commit_button.pack(pady=5)
    
    # Register callbacks
    def on_file_updated(file_path):
        """Update UI when file selection changes."""
        state.selected_file = file_path
        file_monitor.set_file(file_path)
        
        if state.selected_file and os.path.exists(state.selected_file):
            commit_message_entry.config(state=tk.NORMAL)
            commit_button.config(state=tk.NORMAL)
        else:
            commit_message_entry.config(state=tk.DISABLED)
            commit_button.config(state=tk.DISABLED)
        
        update_metadata_display()
    
    shared_state.add_file_callback(on_file_updated)
    
    # Start update loops
    update_time_display()
    check_file_changes()
    
    return frame

import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import logging
from datetime import datetime
import pytz
from time_utils import get_current_times, format_timestamp_dual

APP_NAME = "Inveni"  # Updated app name
SETTINGS_FILE = "settings.json"

# Configure logging with UTC time
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_default_backup_folder():
    """Determine the default backup folder based on platform."""
    system = platform.system()
    username = os.getlogin()
    
    if system == "Windows":
        base_path = os.getenv('LOCALAPPDATA', os.getcwd())
    else:
        base_path = os.path.expanduser("~")
    
    return os.path.join(base_path, APP_NAME, f"backups_{username}")


def load_settings():
    """Load settings with user-specific defaults."""
    username = os.getlogin()
    default_settings = {
        "backup_folder": get_default_backup_folder(),
        "max_backups": 5,
        "logging_enabled": True,
        "username": username,
        "time_format": {
            "utc": "%Y-%m-%d %H:%M:%S",
            "local": "%Y-%m-%d %H:%M:%S %Z"
        }
    }

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding='utf-8') as f:
                settings = json.load(f)
                # Update username if changed
                settings["username"] = username
                
                # Ensure all default keys are present
                updated = False
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                        updated = True
                
                if updated:
                    save_settings(settings)
                
                times = get_current_times()
                logging.info(f"Settings loaded successfully at UTC: {times['utc']}")
                return settings
                
        except json.JSONDecodeError:
            logging.error("Settings file is corrupted. Resetting to defaults.")
            messagebox.showerror("Error", "Settings file is corrupted. Resetting to defaults.")

    save_settings(default_settings)
    return default_settings


def save_settings(settings):
    """Save settings with proper encoding."""
    try:
        with open(SETTINGS_FILE, "w", encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        
        times = get_current_times()
        logging.info(f"Settings saved successfully at UTC: {times['utc']}")
    except Exception as e:
        logging.error(f"Failed to save settings: {str(e)}")
        messagebox.showerror("Error", f"Failed to save settings: {str(e)}")


def settings_page(root, settings, shared_state):
    """Create the Settings page with improved time handling."""
    frame = tk.Frame(root)
    username = os.getlogin()

    def update_time_display():
        """Update the current time display."""
        times = get_current_times()
        current_time_label.config(
            text=(f"Current Time (UTC): {times['utc']}\n"
                  f"Local Time: {times['local']}\n"
                  f"Current User: {username}")
        )
        frame.after(1000, update_time_display)

    def select_backup_folder():
        """Open a folder selection dialog and validate."""
        folder_path = filedialog.askdirectory()
        if folder_path:
            if not os.path.exists(folder_path):
                try:
                    os.makedirs(folder_path)
                    times = get_current_times()
                    logging.info(f"Backup folder created at {times['utc']}: {folder_path}")
                except Exception as e:
                    logging.error(f"Failed to create folder: {str(e)}")
                    messagebox.showerror("Error", f"Failed to create folder: {str(e)}")
                    return
                    
            if os.access(folder_path, os.W_OK):
                settings["backup_folder"] = folder_path
                backup_folder_label.config(text=f"Backup Folder: {folder_path}")
                save_settings(settings)
                messagebox.showinfo("Success", "Backup folder updated successfully!")
            else:
                logging.warning(f"User {username} attempted to set non-writable folder")
                messagebox.showerror("Error", "Selected folder is not writable.")

    def update_max_backups():
        """Update the maximum number of backups."""
        try:
            max_backups_value = int(max_backups_entry.get())
            if max_backups_value <= 0:
                raise ValueError("Max backups must be positive")
            
            settings["max_backups"] = max_backups_value
            save_settings(settings)
            times = get_current_times()
            logging.info(f"Max backups updated to {max_backups_value} at {times['utc']}")
            messagebox.showinfo("Success", "Max backups updated successfully!")
        except ValueError as e:
            logging.error(f"Invalid max backups value: {str(e)}")
            messagebox.showerror("Error", "Please enter a positive number")

    def reset_to_defaults():
        """Reset settings to defaults with confirmation."""
        if messagebox.askyesno("Confirm Reset", 
                              "Reset all settings to defaults?\n\n"
                              f"Current User: {username}\n"
                              f"Time: {get_current_times()['local']}"):
            
            default_settings = {
                "backup_folder": get_default_backup_folder(),
                "max_backups": 5,
                "logging_enabled": True,
                "username": username,
                "time_format": {
                    "utc": "%Y-%m-%d %H:%M:%S",
                    "local": "%Y-%m-%d %H:%M:%S %Z"
                }
            }
            
            settings.update(default_settings)
            save_settings(settings)
            update_ui()
            
            times = get_current_times()
            logging.info(f"Settings reset to defaults at {times['utc']}")
            messagebox.showinfo("Success", "Settings reset to defaults!")

    def view_logs():
        """Display logs with improved time formatting."""
        log_window = tk.Toplevel(root)
        log_window.title("Log Viewer")
        log_window.geometry("800x600")

        # Create frame for time display
        time_frame = tk.Frame(log_window)
        time_frame.pack(fill="x", pady=5)
        
        times = get_current_times()
        tk.Label(time_frame, 
                text=f"Current Time (UTC): {times['utc']}\n"
                     f"Local Time: {times['local']}\n"
                     f"User: {username}").pack()

        # Create Treeview
        tree_frame = tk.Frame(log_window)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add scrollbars
        y_scroll = ttk.Scrollbar(tree_frame)
        y_scroll.pack(side="right", fill="y")
        
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        # Configure Treeview
        tree = ttk.Treeview(
            tree_frame,
            columns=("UTC Time", "Local Time", "Level", "Message"),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )

        # Configure scrollbars
        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)

        # Configure columns
        tree.heading("UTC Time", text="UTC Time")
        tree.heading("Local Time", text="Local Time")
        tree.heading("Level", text="Level")
        tree.heading("Message", text="Message")

        tree.column("UTC Time", width=150, minwidth=150)
        tree.column("Local Time", width=150, minwidth=150)
        tree.column("Level", width=100, minwidth=100)
        tree.column("Message", width=400, minwidth=200)

        tree.pack(side="left", fill="both", expand=True)

        # Load and display logs
        try:
            with open("app.log", "r", encoding='utf-8') as log_file:
                for line in log_file:
                    try:
                        parts = line.strip().split(" - ", 2)
                        if len(parts) == 3:
                            timestamp_str, level, message = parts
                            utc_time, local_time = format_timestamp_dual(timestamp_str)
                            
                            tree.insert("", 0, values=(
                                utc_time,
                                local_time,
                                level,
                                message
                            ))
                    except Exception as e:
                        continue
        except FileNotFoundError:
            messagebox.showinfo("Info", "No logs found")

    def update_ui():
        """Update UI elements with current settings."""
        backup_folder_label.config(text=f"Backup Folder: {settings['backup_folder']}")
        max_backups_entry.delete(0, tk.END)
        max_backups_entry.insert(0, str(settings["max_backups"]))
        logging_var.set(settings["logging_enabled"])

    # UI Setup
    title_label = tk.Label(frame, text="Settings", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    # Current time display
    current_time_label = tk.Label(frame, text="", font=("Arial", 10))
    current_time_label.pack(pady=5)

    # Settings sections
    settings_frame = tk.LabelFrame(frame, text="Backup Settings", padx=10, pady=5)
    settings_frame.pack(fill="x", padx=10, pady=5)

    # Backup folder section
    backup_folder_label = tk.Label(
        settings_frame,
        text=f"Backup Folder: {settings['backup_folder']}",
        font=("Arial", 10),
        fg="gray"
    )
    backup_folder_label.pack(pady=5)
    
    tk.Button(
        settings_frame,
        text="Select Backup Folder",
        command=select_backup_folder
    ).pack(pady=5)

    # Max backups section
    tk.Label(settings_frame, text="Maximum Backups:").pack(pady=5)
    max_backups_entry = tk.Entry(settings_frame, width=10)
    max_backups_entry.pack(pady=5)
    
    tk.Button(
        settings_frame,
        text="Update Max Backups",
        command=update_max_backups
    ).pack(pady=5)

    # Logging section
    logging_frame = tk.LabelFrame(frame, text="Logging Options", padx=10, pady=5)
    logging_frame.pack(fill="x", padx=10, pady=5)

    logging_var = tk.BooleanVar(value=settings.get("logging_enabled", True))
    tk.Checkbutton(
        logging_frame,
        text="Enable Logging",
        variable=logging_var,
        command=lambda: save_settings(settings)
    ).pack(pady=5)

    tk.Button(
        logging_frame,
        text="View Logs",
        command=view_logs
    ).pack(pady=5)

    # Reset button
    tk.Button(
        frame,
        text="Reset to Defaults",
        command=reset_to_defaults,
        fg="red"
    ).pack(pady=10)

    # Start time updates
    update_time_display()
    
    # Initial UI update
    update_ui()

    return frame

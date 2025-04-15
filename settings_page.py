import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import logging

APP_NAME = "MyApp"  # Use a global constant for the application name
SETTINGS_FILE = "settings.json"

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_default_backup_folder():
    """Determine the default backup folder dynamically based on the platform."""
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.getenv('LOCALAPPDATA', os.getcwd()), APP_NAME, "backups")
    else:
        return os.path.expanduser(f"~/.{APP_NAME}/backups")


def load_settings():
    """Load settings from settings.json or return default values."""
    default_settings = {
        "backup_folder": get_default_backup_folder(),
        "max_backups": 5,
        "logging_enabled": True
    }

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                # Ensure all default keys are present
                updated = False
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                        updated = True
                if updated:
                    save_settings(settings)
                logging.info("Settings loaded successfully.")
                return settings
        except json.JSONDecodeError:
            logging.error("Settings file is corrupted. Resetting to defaults.")
            messagebox.showerror("Error", "Settings file is corrupted. Resetting to defaults.")

    save_settings(default_settings)
    logging.info("Default settings loaded.")
    return default_settings


def save_settings(settings):
    """Save settings to settings.json."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        logging.info("Settings saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save settings: {str(e)}")
        messagebox.showerror("Error", f"Failed to save settings: {str(e)}")


def settings_page(root, settings):
    """Create the Settings page."""
    frame = tk.Frame(root)

    def select_backup_folder():
        """Open a folder selection dialog, validate, and update the backup folder setting."""
        folder_path = filedialog.askdirectory()
        if folder_path:
            if not os.path.exists(folder_path):
                try:
                    os.makedirs(folder_path)
                    logging.info(f"Backup folder created: {folder_path}")
                except Exception as e:
                    logging.error(f"Failed to create folder: {str(e)}")
                    messagebox.showerror("Error", f"Failed to create folder: {str(e)}")
                    return
            if os.access(folder_path, os.W_OK):
                settings["backup_folder"] = folder_path
                backup_folder_label.config(text=f"Backup Folder: {folder_path}")
                save_settings(settings)
                logging.info(f"Backup folder updated to: {folder_path}")
                messagebox.showinfo("Success", "Backup folder updated successfully!")
            else:
                logging.warning("The selected folder is not writable.")
                messagebox.showerror("Error", "The selected folder is not writable. Please choose another folder.")

    def update_max_backups():
        """Update the max backups setting."""
        try:
            max_backups_value = int(max_backups_entry.get())
            if max_backups_value <= 0:
                raise ValueError("Max backups must be a positive number.")
            settings["max_backups"] = max_backups_value
            save_settings(settings)
            logging.info(f"Max backups updated to: {max_backups_value}")
            messagebox.showinfo("Success", "Max backups updated successfully!")
        except ValueError:
            logging.error("Invalid number for max backups.")
            messagebox.showerror("Error", "Invalid number for max backups.")

    def toggle_logging():
        """Enable or disable logging."""
        settings["logging_enabled"] = logging_var.get()
        save_settings(settings)
        logging.info(f"Logging preference updated to: {settings['logging_enabled']}")
        messagebox.showinfo("Success", "Logging preference updated successfully!")

    def reset_to_defaults():
        """Reset all settings to their default values."""
        if messagebox.askyesno("Confirmation", "Are you sure you want to reset all settings to defaults?"):
            default_settings = {
                "backup_folder": get_default_backup_folder(),
                "max_backups": 5,
                "logging_enabled": True
            }
            settings.update(default_settings)
            save_settings(settings)
            update_ui()
            logging.info("Settings have been reset to defaults.")
            messagebox.showinfo("Success", "Settings have been reset to defaults.")

    def update_ui():
        """Update the UI elements to match the current settings."""
        backup_folder_label.config(text=f"Backup Folder: {settings['backup_folder']}")
        max_backups_entry.delete(0, tk.END)
        max_backups_entry.insert(0, str(settings["max_backups"]))
        logging_var.set(settings["logging_enabled"])

    def view_logs():
        """Display logs in a new window."""
        log_window = tk.Toplevel()
        log_window.title("Log Viewer")

        # Create Treeview widget to display logs
        tree = ttk.Treeview(log_window, columns=("Timestamp", "Level", "Message"), show="headings")
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Level", text="Level")
        tree.heading("Message", text="Message")
        tree.pack(expand=True, fill="both")

        # Load logs and populate the Treeview
        try:
            with open("app.log", "r") as log_file:
                for line in log_file:
                    parts = line.strip().split(" - ", 2)  # Split log into timestamp, level, and message
                    if len(parts) == 3:
                        tree.insert("", tk.END, values=parts)
        except FileNotFoundError:
            logging.warning("No logs found.")
            messagebox.showinfo("Info", "No logs found.")

        # Add a scrollbar
        scrollbar = tk.Scrollbar(log_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    tk.Label(frame, text="Settings", font=("Arial", 16)).pack(pady=10)
    tk.Label(frame, text="Backup Folder:", font=("Arial", 12)).pack(pady=5)
    backup_folder_label = tk.Label(frame, text=f"Backup Folder: {settings['backup_folder']}", font=("Arial", 10), fg="gray")
    backup_folder_label.pack(pady=5)
    tk.Button(frame, text="Select Backup Folder", command=select_backup_folder).pack(pady=5)

    tk.Label(frame, text="Max Backups:", font=("Arial", 12)).pack(pady=5)
    max_backups_entry = tk.Entry(frame, width=20)
    max_backups_entry.pack(pady=5)
    tk.Button(frame, text="Update Max Backups", command=update_max_backups).pack(pady=5)

    logging_var = tk.BooleanVar(value=settings.get("logging_enabled", True))
    tk.Checkbutton(frame, text="Enable Logging", variable=logging_var, command=toggle_logging).pack(pady=10)

    tk.Button(frame, text="Reset to Defaults", command=reset_to_defaults, fg="red").pack(pady=10)
    tk.Button(frame, text="View Logs", command=view_logs).pack(pady=10)

    update_ui()

    return frame

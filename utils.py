import json
import os

SETTINGS_FILE = "settings.json"
TRACKED_FILES_PATH = "tracked_files.json"

def load_settings():
    """Load settings from settings.json or return default values."""
    default_settings = {"backup_folder": "backups", "max_backups": 5}

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                # Ensure backup_folder is present in the settings
                if "backup_folder" not in settings:
                    settings["backup_folder"] = default_settings["backup_folder"]
                    save_settings(settings)
                return settings
        except (json.JSONDecodeError, ValueError):
            print("Error: settings.json is corrupted. Resetting to default settings.")

    # Reset to default settings and save the file
    save_settings(default_settings)
    return default_settings

def save_settings(settings):
    """Save settings to settings.json."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

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
import json
import os

APP_NAME = "MyApp"
BASE_DIR = os.path.join(os.getenv('LOCALAPPDATA', os.getcwd()), APP_NAME)  # Configurable base directory

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
TRACKED_FILES_PATH = os.path.join(BASE_DIR, "tracked_files.json")

def validate_settings(settings):
    """Ensure the settings have all required keys and valid values."""
    default_settings = {"backup_folder": "backups", "max_backups": 5, "logging_enabled": True}
    for key, value in default_settings.items():
        if key not in settings:
            settings[key] = value
    return settings

def load_settings():
    """Load settings from settings.json or return default values."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                return validate_settings(settings)
        except (json.JSONDecodeError, ValueError):
            print("Error: settings.json is corrupted. Resetting to default settings.")

    # Reset to default settings and save the file
    default_settings = {"backup_folder": "backups", "max_backups": 5, "logging_enabled": True}
    save_settings(default_settings)
    return default_settings

def save_settings(settings):
    """Save settings to settings.json."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error: Failed to save settings. {str(e)}")

def load_tracked_files():
    """Load tracked file metadata from JSON."""
    if not os.path.exists(TRACKED_FILES_PATH):
        return {}

    try:
        with open(TRACKED_FILES_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("Invalid tracked files structure. Expected a dictionary.")
            return data
    except (json.JSONDecodeError, ValueError):
        print("Error: tracked_files.json is corrupted. Returning an empty dictionary.")
        return {}

def save_tracked_files(tracked_files):
    """Save tracked file metadata to JSON."""
    try:
        with open(TRACKED_FILES_PATH, "w", encoding="utf-8") as file:
            json.dump(tracked_files, file, indent=4)
    except Exception as e:
        print(f"Error: Failed to save tracked files. {str(e)}")

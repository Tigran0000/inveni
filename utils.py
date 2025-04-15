import os
import json
import gzip
import hashlib
from tkinter import filedialog, messagebox
import datetime
from typing import Optional, Dict, Any


def log_error(error_message: str) -> None:
    """Log error messages to a file with a timestamp."""
    log_file_path = os.path.join(os.getcwd(), "error_log.txt")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a") as log_file:
        log_file.write(f"[{timestamp}] {error_message}\n")


def load_tracked_files() -> Dict[str, Any]:
    """Load tracked files from tracked_files.json."""
    try:
        with open("tracked_files.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        log_error("Error: tracked_files.json not found.")
        return {}
    except json.JSONDecodeError:
        log_error("Error: tracked_files.json is corrupted or improperly formatted.")
        messagebox.showerror("Error", "The tracked files data is corrupted. Please check the file.")
        return {}


def save_tracked_files(tracked_files: Dict[str, Any]) -> None:
    """Save tracked files to tracked_files.json."""
    try:
        with open("tracked_files.json", "w") as file:
            json.dump(tracked_files, file, indent=4)
    except Exception as e:
        log_error(f"Error: Failed to save tracked files: {str(e)}")
        messagebox.showerror("Error", "Failed to save tracked files. Please check your permissions.")


def calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as file:
            while chunk := file.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except FileNotFoundError:
        log_error(f"Error: File not found for hashing: {file_path}")
        return None


def restore_file_version(file_path: str, file_hash: str, backup_folder: str) -> None:
    """
    Restore a specific version of a file based on its hash.

    :param file_path: The original file path to restore.
    :param file_hash: The hash of the file version to restore.
    :param backup_folder: The root backup folder where file-specific backups are stored.
    """
    try:
        # Normalize the file path
        normalized_file_path = os.path.normpath(file_path)

        # Extract the base file name (e.g., z.txt)
        base_file_name = os.path.basename(normalized_file_path)

        # Construct the file-specific backup folder path
        # ENSURE NO DUPLICATE APPENDING OF base_file_name
        file_backup_folder = os.path.join(backup_folder, base_file_name)

        # DEBUG: Log the constructed folder path
        print(f"DEBUG: Backup folder: {file_backup_folder}")

        # Construct the backup file path using the hash
        backup_file_path = os.path.join(file_backup_folder, f"{base_file_name}_{file_hash}.gz")

        # DEBUG: Log the constructed file path
        print(f"Restoring from Backup File Path: {backup_file_path}")

        # Check if the backup file exists
        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")

        # Decompress and restore the file
        with gzip.open(backup_file_path, "rb") as src, open(normalized_file_path, "wb") as dest:
            dest.write(src.read())

        messagebox.showinfo("Success", f"File restored successfully!\n\nFile: {normalized_file_path}")

    except FileNotFoundError as e:
        error_message = f"Error: {str(e)}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)
        raise
    except gzip.BadGzipFile:
        error_message = f"Error: The backup file is corrupted: {backup_file_path}"
        log_error(error_message)
        messagebox.showerror("Error", "The backup file is corrupted and cannot be restored.")
        raise
    except Exception as e:
        error_message = f"Error: Unexpected error during restore: {str(e)}"
        log_error(error_message)
        messagebox.showerror("Error", "An unexpected error occurred while restoring the file.")
        raise

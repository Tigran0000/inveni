import os
import json
import hashlib
import datetime

TRACKED_FILES_PATH = "tracked_files.json"
BACKUP_ROOT = "backups"

def ensure_backup_directory():
    """Ensure the backup directory exists."""
    if not os.path.exists(BACKUP_ROOT):
        os.makedirs(BACKUP_ROOT)

def load_tracked_files():
    """Load tracked file metadata from JSON."""
    if not os.path.exists(TRACKED_FILES_PATH):
        return {}
    with open(TRACKED_FILES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

def save_tracked_files(tracked_files):
    """Save tracked file metadata to JSON."""
    with open(TRACKED_FILES_PATH, "w", encoding="utf-8") as file:
        json.dump(tracked_files, file, indent=4)

def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def create_backup(file_path):
    """Create a zip backup of the file."""
    ensure_backup_directory()
    file_name = os.path.basename(file_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_name = f"{file_name}_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_ROOT, backup_name)

    with zipfile.ZipFile(backup_path, "w") as zipf:
        zipf.write(file_path, arcname=file_name)
    print(f"Backup created: {backup_path}")

def commit_file(file_path, commit_message, username):
    """Commit a file by tracking its metadata and changes."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    tracked_files = load_tracked_files()
    file_hash = calculate_file_hash(file_path)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if the file is already tracked and has changed
    if file_path in tracked_files:
        last_hash = tracked_files[file_path]["hash"]
        if last_hash == file_hash:
            print(f"No changes detected for {file_path}. Commit skipped.")
            return

    # Add or update file metadata
    tracked_files[file_path] = {
        "hash": file_hash,
        "timestamp": timestamp,
        "commit_message": commit_message,
        "username": username
    }

    save_tracked_files(tracked_files)
    print(f"File committed: {file_path}")

    # Automatically back up the file
    print(f"Backing up the file: {file_path}")
    create_backup(file_path)

if __name__ == "__main__":
    # Example usage
    commit_file("example.txt", "Initial commit", "Tigran0000")
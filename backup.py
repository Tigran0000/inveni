import os
import hashlib
import zipfile
import datetime
import json
import threading

BACKUP_DIR = "backups"
BACKUP_QUOTA = 10  # Maximum number of backups to keep
METADATA_FILE = os.path.join(BACKUP_DIR, "metadata.json")


def ensure_backup_directory():
    """Ensure the backup directory exists."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_metadata():
    """Load backup metadata."""
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, "r") as f:
        return json.load(f)


def save_metadata(metadata):
    """Save backup metadata."""
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)


def create_backup(file_path):
    """Create a compressed backup of a file."""
    ensure_backup_directory()
    metadata = load_metadata()

    file_name = os.path.basename(file_path)
    file_hash = calculate_file_hash(file_path)

    # Check if the file has already been backed up
    if file_name in metadata and metadata[file_name]["hash"] == file_hash:
        print(f"No changes detected for: {file_name}. Skipping backup.")
        return

    # Create a new backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_name = f"{file_name}_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, arcname=file_name)

    print(f"Backup created: {backup_path}")

    # Update metadata
    metadata[file_name] = {"hash": file_hash, "last_backup": timestamp}
    save_metadata(metadata)

    enforce_backup_quota()


def enforce_backup_quota():
    """Enforce the backup quota by deleting the oldest backups."""
    backups = sorted(
        [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")],
        key=os.path.getctime
    )
    while len(backups) > BACKUP_QUOTA:
        oldest_backup = backups.pop(0)
        os.remove(oldest_backup)
        print(f"Deleted old backup: {oldest_backup}")


def backup_files_in_parallel(file_paths):
    """Backup multiple files in parallel."""
    threads = []
    for file_path in file_paths:
        thread = threading.Thread(target=create_backup, args=(file_path,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    # Example usage: python backup.py <file_path1> <file_path2> ...
    import sys
    if len(sys.argv) < 2:
        print("Usage: python backup.py <file_path1> <file_path2> ...")
        sys.exit(1)

    file_paths = sys.argv[1:]
    backup_files_in_parallel(file_paths)
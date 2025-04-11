import os
import zipfile
import sys

BACKUP_ROOT = r"C:\Users\User\Documents\nnn\backups"

def list_file_versions(file_name_safe):
    """
    List all available backup versions for a given file.
    """
    if not os.path.exists(BACKUP_ROOT):
        print(f"Error: Backup directory not found: {BACKUP_ROOT}")
        return []

    # Find all backup files for the given file name
    backup_files = [f for f in os.listdir(BACKUP_ROOT) if f.startswith(file_name_safe) and f.endswith(".zip")]

    if not backup_files:
        print(f"No backups found for {file_name_safe}")
        return []

    # Sort backups by timestamp in the filename
    backup_files.sort()
    return backup_files

def restore_file(file_path, version=None):
    """
    Restore a specific version of a file or the latest version if none is specified.
    """
    if not os.path.exists(BACKUP_ROOT):
        print(f"Error: Backup directory not found: {BACKUP_ROOT}")
        return

    # Generate the safe name based on the original file path
    file_name_safe = file_path.replace("\\", "_").replace("/", "_").replace(":", "")
    # Get all available backups for the given file
    backup_files = list_file_versions(file_name_safe)

    if not backup_files:
        print(f"No backups found for {file_path}.")
        return

    # If no version is specified, restore the latest one
    if version is None:
        version = backup_files[-1]

    # Check if the specified version exists
    if version not in backup_files:
        print(f"Error: Specified version '{version}' not found for {file_path}")
        return

    backup_path = os.path.join(BACKUP_ROOT, version)
    try:
        # Extract the backup file to the file's original directory
        with zipfile.ZipFile(backup_path, "r") as zipf:
            zipf.extractall(os.path.dirname(file_path))
        print(f"File restored: {file_path} from backup {backup_path}")
    except Exception as e:
        print(f"Error during restoration: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: InveniRestore.exe <file_path> [version]")
        sys.exit(1)

    file_path = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None

    if version:
        print(f"Restoring version '{version}' of {file_path}...")
    else:
        print(f"Restoring the latest version of {file_path}...")

    restore_file(file_path, version)
import os
import json
import gzip
import shutil
import hashlib
from datetime import datetime
import pytz
from typing import Dict, Any, Optional, List, Tuple
from time_utils import get_current_times, format_timestamp_dual


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of file contents."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        log_error(f"Failed to calculate file hash: {str(e)}")
        raise


def has_file_changed(file_path: str, tracked_files: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Check if file has changed from its last tracked version.
    Returns (has_changed, current_hash, last_hash)
    """
    try:
        current_hash = calculate_file_hash(file_path)
        normalized_path = os.path.normpath(file_path)
        
        if normalized_path not in tracked_files:
            return True, current_hash, ""
            
        versions = tracked_files[normalized_path].get("versions", {})
        if not versions:
            return True, current_hash, ""
            
        # Get most recent version hash
        latest_version = sorted(
            versions.items(),
            key=lambda x: datetime.strptime(x[1]["timestamp"], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )[0]
        
        last_hash = latest_version[0]
        return current_hash != last_hash, current_hash, last_hash
        
    except Exception as e:
        log_error(f"Failed to check file changes: {str(e)}")
        raise


def get_temp_backup_path(file_path: str, backup_folder: str) -> str:
    """Get path for temporary .bak file in backup folder."""
    base_name = os.path.basename(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(backup_folder, "temp_backups")
    os.makedirs(backup_dir, exist_ok=True)
    return os.path.join(backup_dir, f"{base_name}.{timestamp}.bak")


def log_error(error_message: str) -> None:
    """Log error messages with UTC timestamp."""
    log_file_path = os.path.join(os.getcwd(), "error_log.txt")
    current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")
    username = os.getlogin()
    
    with open(log_file_path, "a", encoding='utf-8') as log_file:
        log_file.write(f"[{current_time}] [{username}] {error_message}\n")


def load_tracked_files() -> Dict[str, Any]:
    """Load tracked files from JSON."""
    try:
        with open("tracked_files.json", "r", encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        log_error("Error: tracked_files.json is corrupted.")
        return {}


def save_tracked_files(tracked_files: Dict[str, Any]) -> None:
    """Save tracked files to JSON with proper formatting."""
    try:
        with open("tracked_files.json", "w", encoding='utf-8') as file:
            json.dump(tracked_files, file, indent=4, ensure_ascii=False)
    except Exception as e:
        log_error(f"Failed to save tracked files: {str(e)}")
        raise


def get_backup_path(file_path: str, file_hash: str, backup_folder: str) -> str:
    """Construct the backup file path."""
    base_name = os.path.basename(file_path)
    version_dir = os.path.join(backup_folder, "versions", base_name)
    os.makedirs(version_dir, exist_ok=True)
    return os.path.join(version_dir, f"{file_hash}.gz")


def clean_old_backups(file_path: str, backup_folder: str, max_backups: int, tracked_files: Dict) -> None:
    """Clean up old backups keeping only the most recent ones."""
    try:
        normalized_path = os.path.normpath(file_path)
        base_name = os.path.basename(normalized_path)
        version_dir = os.path.join(backup_folder, "versions", base_name)
        
        if not os.path.exists(version_dir):
            return

        if normalized_path not in tracked_files:
            return
            
        versions = tracked_files[normalized_path]["versions"]
        if not versions:
            return

        # Sort versions by timestamp (newest first)
        sorted_versions = sorted(
            versions.items(),
            key=lambda x: datetime.strptime(x[1]["timestamp"], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )

        # Keep only max_backups number of versions
        versions_to_keep = sorted_versions[:max_backups]
        versions_to_delete = sorted_versions[max_backups:]

        # Remove old backups and their entries
        for version_hash, _ in versions_to_delete:
            backup_path = get_backup_path(normalized_path, version_hash, backup_folder)
            if os.path.exists(backup_path):
                os.remove(backup_path)
            del tracked_files[normalized_path]["versions"][version_hash]

        # Clean up old .bak files
        temp_backup_dir = os.path.join(backup_folder, "temp_backups")
        if os.path.exists(temp_backup_dir):
            current_time = datetime.now()
            for filename in os.listdir(temp_backup_dir):
                if filename.startswith(base_name) and filename.endswith('.bak'):
                    file_path = os.path.join(temp_backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_time).days >= 1:
                        os.remove(file_path)

        save_tracked_files(tracked_files)

    except Exception as e:
        log_error(f"Failed to clean old backups: {str(e)}")
        raise


def create_backup(file_path: str, file_hash: str, backup_folder: str, settings: dict) -> str:
    """Create a compressed backup and manage backup count."""
    try:
        backup_path = get_backup_path(file_path, file_hash, backup_folder)
        
        # Create compressed backup
        with open(file_path, 'rb') as src, gzip.open(backup_path, 'wb') as dst:
            shutil.copyfileobj(src, dst)

        tracked_files = load_tracked_files()
        max_backups = settings.get('max_backups', 5)
        clean_old_backups(file_path, backup_folder, max_backups, tracked_files)

        return backup_path

    except Exception as e:
        log_error(f"Failed to create backup: {str(e)}")
        raise


def get_backup_count(file_path: str, backup_folder: str) -> int:
    """Get the current number of backups for a file."""
    try:
        normalized_path = os.path.normpath(file_path)
        base_name = os.path.basename(normalized_path)
        version_dir = os.path.join(backup_folder, "versions", base_name)
        
        if not os.path.exists(version_dir):
            return 0
            
        return len([f for f in os.listdir(version_dir) if f.endswith('.gz')])
    except Exception:
        return 0


def restore_file_version(file_path: str, file_hash: str, backup_folder: str) -> None:
    """Restore a specific version of a file."""
    try:
        normalized_path = os.path.normpath(file_path)
        backup_path = get_backup_path(normalized_path, file_hash, backup_folder)

        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Create backup of current file in temp backup folder
        temp_backup_path = get_temp_backup_path(normalized_path, backup_folder)
        if os.path.exists(normalized_path):
            shutil.copy2(normalized_path, temp_backup_path)

        # Restore from backup
        with gzip.open(backup_path, 'rb') as src, open(normalized_path, 'wb') as dst:
            shutil.copyfileobj(src, dst)

    except Exception as e:
        log_error(f"Restore failed: {str(e)}")
        raise


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """Get detailed file metadata."""
    try:
        stat = os.stat(file_path)
        username = os.getlogin()
        
        # Get current times
        current_times = get_current_times()
        
        return {
            "size": stat.st_size,
            "creation_time": {
                "utc": datetime.utcfromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "local": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S %Z")
            },
            "modification_time": {
                "utc": datetime.utcfromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "local": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S %Z")
            },
            "current_time": current_times,
            "file_type": os.path.splitext(file_path)[1].lower() or "unknown",
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK),
            "username": username
        }
    except Exception as e:
        log_error(f"Failed to get file metadata: {str(e)}")
        return {
            "size": 0,
            "creation_time": {"utc": "Unknown", "local": "Unknown"},
            "modification_time": {"utc": "Unknown", "local": "Unknown"},
            "current_time": get_current_times(),
            "file_type": "unknown",
            "is_readable": False,
            "is_writable": False,
            "username": username
        }


def cleanup_old_bak_files(backup_folder: str) -> None:
    """Clean up .bak files older than 24 hours."""
    try:
        temp_backup_dir = os.path.join(backup_folder, "temp_backups")
        if not os.path.exists(temp_backup_dir):
            return

        current_time = datetime.now()
        for filename in os.listdir(temp_backup_dir):
            if filename.endswith('.bak'):
                file_path = os.path.join(temp_backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if (current_time - file_time).days >= 1:
                    os.remove(file_path)
    except Exception as e:
        log_error(f"Failed to cleanup old .bak files: {str(e)}")

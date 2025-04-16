import os
from datetime import datetime
from typing import Callable, Optional
from utils import calculate_file_hash

class FileMonitor:
    def __init__(self, callback: Callable[[str, bool], None]):
        self.watched_file: Optional[str] = None
        self.last_hash: Optional[str] = None
        self.last_check: Optional[float] = None
        self.callback = callback

    def set_file(self, file_path: Optional[str]) -> None:
        """Set or change the watched file."""
        self.watched_file = file_path
        if file_path and os.path.exists(file_path):
            self.last_hash = calculate_file_hash(file_path)
            self.last_check = os.path.getmtime(file_path)
        else:
            self.last_hash = None
            self.last_check = None

    def check_for_changes(self) -> None:
        """Check if the watched file has changed."""
        if not self.watched_file or not os.path.exists(self.watched_file):
            return

        current_mtime = os.path.getmtime(self.watched_file)
        if current_mtime != self.last_check:
            current_hash = calculate_file_hash(self.watched_file)
            has_changed = current_hash != self.last_hash
            self.last_hash = current_hash
            self.last_check = current_mtime
            self.callback(self.watched_file, has_changed)
import os
from typing import Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileVersion:
    """Data structure for file version information."""
    hash: str
    timestamp: str
    commit_message: str
    username: str


class SharedState:
    """Shared state to synchronize file selection and version updates across pages."""
    def __init__(self):
        self.selected_file: Optional[str] = None
        self.file_callbacks: List[Callable[[Optional[str]], None]] = []
        self.version_callbacks: List[Callable[[], None]] = []
        self.last_update: Optional[datetime] = None
        self.current_user: str = "Tigran0000"  # Fixed username
        self._active = True  # Flag to track if callbacks should be processed

    def set_selected_file(self, file_path: Optional[str]) -> None:
        """
        Set the selected file and notify all file selection listeners.
        
        Args:
            file_path: The path to the selected file or None if no file is selected
        """
        if file_path is None:
            self.selected_file = None
        else:
            try:
                normalized_path = os.path.normpath(file_path)
                if os.path.exists(normalized_path):
                    self.selected_file = normalized_path
                else:
                    print(f"Warning: File does not exist: {normalized_path}")
                    self.selected_file = None
            except Exception as e:
                print(f"Error normalizing path: {str(e)}")
                self.selected_file = None

        if self._active:
            self._notify_file_callbacks()

    def get_selected_file(self) -> Optional[str]:
        """Get the currently selected file path."""
        if self.selected_file and os.path.exists(self.selected_file):
            return self.selected_file
        return None

    def notify_version_change(self) -> None:
        """
        Notify all version change listeners that a new version has been committed.
        This should be called after a successful commit.
        """
        self.last_update = datetime.now()
        if self._active:
            self._notify_version_callbacks()

    def add_file_callback(self, callback: Callable[[Optional[str]], None]) -> None:
        """
        Add a callback to be triggered when the selected file changes.
        
        Args:
            callback: Function to be called when file selection changes
        """
        if callback not in self.file_callbacks:
            self.file_callbacks.append(callback)
            # Trigger callback immediately with current state
            if self._active:
                try:
                    callback(self.get_selected_file())
                except Exception as e:
                    print(f"Error in initial file callback: {str(e)}")

    def add_version_callback(self, callback: Callable[[], None]) -> None:
        """
        Add a callback to be triggered when a new version is committed.
        
        Args:
            callback: Function to be called when a new version is committed
        """
        if callback not in self.version_callbacks:
            self.version_callbacks.append(callback)

    def _notify_file_callbacks(self) -> None:
        """Notify all registered file selection callbacks."""
        current_file = self.get_selected_file()
        for callback in self.file_callbacks:
            try:
                callback(current_file)
            except Exception as e:
                print(f"Error in file callback: {str(e)}")

    def _notify_version_callbacks(self) -> None:
        """Notify all registered version change callbacks."""
        for callback in self.version_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in version callback: {str(e)}")

    def remove_callback(self, callback: Callable) -> None:
        """
        Remove a callback from both file and version callbacks.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self.file_callbacks:
            self.file_callbacks.remove(callback)
        if callback in self.version_callbacks:
            self.version_callbacks.remove(callback)

    def pause_callbacks(self) -> None:
        """Temporarily pause callback notifications."""
        self._active = False

    def resume_callbacks(self) -> None:
        """Resume callback notifications and trigger updates."""
        self._active = True
        self._notify_file_callbacks()
        if self.last_update:
            self._notify_version_callbacks()

    def is_file_selected(self) -> bool:
        """Check if a valid file is currently selected."""
        return bool(self.get_selected_file())

import os

class SharedState:
    """Shared state to synchronize file selection across pages."""
    def __init__(self):
        self.selected_file = None
        self.callbacks = []

    def set_selected_file(self, file_path):
        """Set the selected file and notify all listeners."""
        self.selected_file = os.path.normpath(file_path) if file_path else None
        for callback in self.callbacks:
            callback(self.selected_file)

    def get_selected_file(self):
        """Get the currently selected file."""
        return self.selected_file

    def add_callback(self, callback):
        """Add a callback to be triggered when the selected file changes."""
        self.callbacks.append(callback)

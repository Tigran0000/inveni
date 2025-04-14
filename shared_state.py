class SharedState:
    """Shared state to synchronize file selection across pages."""
    def __init__(self):
        self.selected_file = None
        self.callbacks = []

    def set_selected_file(self, file_path):
        """Set the selected file and notify all listeners."""
        self.selected_file = file_path
        for callback in self.callbacks:
            callback(file_path)

    def get_selected_file(self):
        """Get the currently selected file."""
        return self.selected_file

    def add_callback(self, callback):
        """Add a callback to be triggered when the selected file changes."""
        self.callbacks.append(callback)
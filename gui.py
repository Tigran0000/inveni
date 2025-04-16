import tkinter as tk
from tkinter import ttk
import os
from datetime import datetime
import pytz
from settings_page import settings_page, load_settings
from gui_commit_page import commit_page
from restore_page import restore_page
from shared_state import SharedState


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Inveni File Version Manager")
        
        # Load settings
        self.settings = load_settings()
        
        # Initialize shared state
        self.shared_state = SharedState()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        self.commit_frame = commit_page(self.notebook, self.settings, self.shared_state)
        self.restore_frame = restore_page(self.notebook, self.settings, self.shared_state)
        self.settings_frame = settings_page(self.notebook, self.settings, self.shared_state)
        
        # Add tabs to notebook
        self.notebook.add(self.commit_frame, text='Commit')
        self.notebook.add(self.restore_frame, text='Restore')
        self.notebook.add(self.settings_frame, text='Settings')
        
        # Configure window size and position
        window_width = 800
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        
        # Set window size and position
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Add window title with version
        self.root.title("Inveni - File Version Manager v1.0")
        
        # Add status bar
        self.status_bar = tk.Label(
            root,
            text=self.get_status_text(),
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Update status bar every second
        self.update_status_bar()

    def get_status_text(self):
        """Get formatted status bar text."""
        current_time_utc = datetime.now(pytz.UTC)
        current_time_local = current_time_utc.astimezone()
        username = os.getlogin()
        
        return (
            f"UTC: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Local: {current_time_local.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
            f"User: {username}"
        )

    def update_status_bar(self):
        """Update the status bar text."""
        self.status_bar.config(text=self.get_status_text())
        self.root.after(1000, self.update_status_bar)


def main():
    try:
        root = tk.Tk()
        app = MainApplication(root)
        root.mainloop()
    except Exception as e:
        # Log the error with current time
        current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        error_message = f"{current_time} - ERROR - Application failed to start: {str(e)}\n"
        
        # Write to error log
        with open("error.log", "a", encoding='utf-8') as f:
            f.write(error_message)
        
        # Re-raise the exception
        raise


if __name__ == "__main__":
    main()

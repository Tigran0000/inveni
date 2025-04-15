import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from settings_page import settings_page, load_settings  # Import the settings loader and UI
from shared_state import SharedState  # Shared state to synchronize file selection
from gui_commit_page import commit_page  # Commit page functionality
from restore_page import restore_page  # Restore page functionality


def main():
    # Load settings (e.g., backup folder, max backups)
    settings = load_settings()

    # Create a shared state instance
    shared_state = SharedState()

    # Check if a command-line argument for pre-selected file is provided
    if len(sys.argv) > 1:
        preselected_file = sys.argv[1]
        # Ensure the file exists before setting it in SharedState
        if os.path.exists(preselected_file):
            shared_state.set_selected_file(preselected_file)
        else:
            # Show an error message if the file does not exist
            messagebox.showerror("Error", f"The file '{preselected_file}' does not exist.")
            shared_state.set_selected_file(None)

    # Create the main Tkinter window
    root = tk.Tk()
    root.title("File Version Manager")

    # Create a notebook (tabbed interface)
    notebook = ttk.Notebook(root)

    # Add Commit, Restore, and Settings pages
    commit_frame = commit_page(notebook, settings, shared_state)
    restore_frame = restore_page(notebook, settings, shared_state)
    settings_frame = settings_page(notebook, settings)  # Add the Settings page

    notebook.add(commit_frame, text="Commit")
    notebook.add(restore_frame, text="Restore")
    notebook.add(settings_frame, text="Settings")  # Add a new "Settings" tab
    notebook.pack(expand=1, fill="both")

    # Synchronize UI with preselected file
    def initialize_ui():
        selected_file = shared_state.get_selected_file()
        if selected_file:
            # Notify both pages about the preselected file
            for callback in shared_state.callbacks:
                callback(selected_file)
            # Update the window title to include the selected file
            root.title(f"File Version Manager - {os.path.basename(selected_file)}")

    # Initialize UI after rendering
    root.after(100, initialize_ui)

    # Start the Tkinter main loop
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Log the error to a file
        log_file_path = os.path.join(os.getcwd(), "error_log.txt")
        with open(log_file_path, "a") as log_file:
            log_file.write(f"Error: {str(e)}\n")
        # Show the error message to the user
        messagebox.showerror("Critical Error", str(e))
        sys.exit(1)

import os
import sys
import tkinter as tk
from tkinter import ttk
from shared_state import SharedState
from gui_commit_page import commit_page
from restore_page import restore_page
from settings_page import settings_page, load_settings

def main():
    # Create a shared state for file selection
    shared_state = SharedState()

    # Load settings
    settings = load_settings()

    # Create the main Tkinter window
    root = tk.Tk()
    root.title("File Manager GUI")
    root.geometry("600x400")

    # Create a Notebook (tabbed interface)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Add pages to the Notebook
    notebook.add(commit_page(root, settings, shared_state), text="Commit")
    notebook.add(restore_page(root, settings, shared_state), text="Restore")
    notebook.add(settings_page(root, settings), text="Settings")

    # Start the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()

import os
import sys
import tkinter as tk
from tkinter import ttk
from gui_commit_page import commit_page
from restore_page import restore_page
from settings_page import settings_page, load_settings

def main():
    # Check for a file path passed as an argument
    preselected_file = None
    if len(sys.argv) > 1:
        preselected_file = sys.argv[1]
        if not os.path.exists(preselected_file):
            print(f"Error: The selected file does not exist: {preselected_file}")
            preselected_file = None

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
    notebook.add(commit_page(root, settings, preselected_file), text="Commit")
    notebook.add(restore_page(root, settings, preselected_file), text="Restore")
    notebook.add(settings_page(root, settings, preselected_file), text="Settings")

    # Start the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()

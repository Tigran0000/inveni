import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable


class TagDialog:
    def __init__(self, parent, current_tags: List[str], 
                 on_save: Callable[[List[str]], None]):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Tags")
        self.dialog.geometry("300x400")
        self.current_tags = current_tags
        self.on_save = on_save

        self.setup_ui()

    def setup_ui(self):
        # Tags list
        tk.Label(self.dialog, text="Current Tags:").pack(pady=5)
        
        self.tags_frame = tk.Frame(self.dialog)
        self.tags_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tags_list = tk.Listbox(self.tags_frame, selectmode=tk.MULTIPLE)
        self.tags_list.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.tags_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.tags_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tags_list.yview)

        # New tag entry
        tk.Label(self.dialog, text="New Tag:").pack(pady=5)
        self.new_tag_entry = tk.Entry(self.dialog)
        self.new_tag_entry.pack(pady=5)

        # Buttons
        buttons_frame = tk.Frame(self.dialog)
        buttons_frame.pack(fill="x", pady=10)

        tk.Button(buttons_frame, text="Add Tag", 
                 command=self.add_tag).pack(side="left", padx=5)
        tk.Button(buttons_frame, text="Remove Selected", 
                 command=self.remove_selected).pack(side="left", padx=5)
        tk.Button(buttons_frame, text="Save", 
                 command=self.save_tags).pack(side="right", padx=5)

        # Initialize tags list
        self.refresh_tags_list()

    def refresh_tags_list(self):
        self.tags_list.delete(0, tk.END)
        for tag in sorted(self.current_tags):
            self.tags_list.insert(tk.END, tag)

    def add_tag(self):
        new_tag = self.new_tag_entry.get().strip().lower()
        if new_tag:
            if new_tag not in self.current_tags:
                self.current_tags.append(new_tag)
                self.refresh_tags_list()
            self.new_tag_entry.delete(0, tk.END)

    def remove_selected(self):
        selected_indices = self.tags_list.curselection()
        for i in reversed(selected_indices):
            tag = self.tags_list.get(i)
            self.current_tags.remove(tag)
        self.refresh_tags_list()

    def save_tags(self):
        self.on_save(self.current_tags)
        self.dialog.destroy()
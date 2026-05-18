import customtkinter as ctk

class tool_window(ctk.CTkToplevel):
    def __init__(self, master_root, window_title_text: str, window_size_text: str = '800x560'):
        super().__init__(master_root)
        self.title(window_title_text)
        self.geometry(window_size_text)
        self.minsize(680, 450)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

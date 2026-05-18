import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the toolkit package directory to sys.path to ensure seamless absolute/relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, "toolkit"))

def main():
    try:
        import customtkinter as ctk
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependency", "CustomTkinter is not installed.\nPlease run: pip install customtkinter")
        return

    try:
        from toolkit.windows.dashboard_window import DashboardWindow
    except ImportError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Import Error", f"Failed to import Dashboard:\n{e}")
        return

    try:
        app = DashboardWindow()
        app.mainloop()
    except Exception as e:
        ctk.set_appearance_mode("System")
        messagebox.showerror("Runtime Error", f"An error occurred:\n{e}")

if __name__ == "__main__":
    main()

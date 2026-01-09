"""
dialogs.py
Các helper dialog / utility UI dùng trong nhiều view:
- center_window: căn giữa một Toplevel
- show_info, show_error, ask_confirm: wrapper messagebox
"""
import customtkinter as ctk
from tkinter import messagebox

def center_window(win, width, height):
    """Căn giữa cửa sổ win với kích thước width x height"""
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

def show_info(title, message):
    messagebox.showinfo(title, message)

def show_error(title, message):
    messagebox.showerror(title, message)

def ask_confirm(title, message):
    return messagebox.askyesno(title, message)
# Thay thế toàn bộ file hrm_app/dialogs.py bằng nội dung dưới nếu bạn dùng custom popups

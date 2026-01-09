# hrm_app/views/departments.py
# Cập nhật: double-click vào phòng ban sẽ mở dialog liệt kê nhân viên ở phòng ban đó
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from ..dialogs import center_window, show_info, show_error, ask_confirm

class DepartmentsView:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def render(self):
        header = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0,14))
        if self.app.is_admin:
            add_btn = ctk.CTkButton(header, text="➕ Thêm phòng ban", fg_color="#4f46e5", hover_color="#4338ca",
                                    command=self.open_add_dialog)
            add_btn.pack(side="right", padx=4)

        table_frame = ctk.CTkFrame(self.app.content_frame, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID","Tên phòng ban","Mô tả")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=34, font=('Inter', 11))
        style.configure("Treeview.Heading", background="#4f46e5", foreground="white", font=('Inter', 11, 'bold'))

        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Tên phòng ban", width=320)
        self.tree.column("Mô tả", width=520)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y", pady=12, padx=(0,12))

        self.load_departments()

        # Context menu (right-click) - chỉ khi is_admin
        if self.app.is_admin:
            self.tree.bind("<Button-3>", self.on_right_click)

        # Double-click -> mở dialog hiển thị nhân viên thuộc phòng ban
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_departments(self):
        self.tree.delete(*self.tree.get_children())
        depts = self.db.get_all_departments()
        for d in depts:
            self.tree.insert("", "end", values=d)

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="✏️ Sửa", command=self.open_edit_dialog)
        menu.add_command(label="🗑️ Xóa", command=self.delete_selected)
        menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        """Khi double-click 1 phòng ban: mở dialog liệt kê nhân viên trong phòng ban đó"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item)['values']
        dept_id, dept_name = values[0], values[1]
        # Lấy danh sách nhân viên của phòng ban
        staffs = self.db.get_staffs_by_department(dept_id)

        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Nhân viên thuộc {dept_name}")
        center_window(dialog, 700, 480)
        dialog.transient(self.app)
        dialog.grab_set()

        # Treeview hiển thị nhân viên
        cols = ("ID","STT","Họ và tên","Vị trí","Điện thoại","Ngày sinh")
        tree = ttk.Treeview(dialog, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=50, anchor="center")
        tree.column("STT", width=60, anchor="center")
        tree.column("Họ và tên", width=220)
        tree.column("Vị trí", width=160)
        tree.column("Điện thoại", width=120, anchor="center")
        tree.column("Ngày sinh", width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=12, pady=12)

        for s in staffs:
            # s = (id, stt, full_name, position, phone, dob, dept_name)
            tree.insert("", "end", values=(s[0], s[1], s[2], s[3], s[4], s[5]))

    def open_add_dialog(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Thêm phòng ban mới")
        dialog.geometry("500x300")
        center_window(dialog, 500, 300)
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tên phòng ban:", font=ctk.CTkFont(size=13, weight="bold")).pack(padx=16, pady=(20,6), anchor="w")
        name_entry = ctk.CTkEntry(dialog, height=36)
        name_entry.pack(padx=16, fill="x")

        ctk.CTkLabel(dialog, text="Mô tả:", font=ctk.CTkFont(size=13, weight="bold")).pack(padx=16, pady=(12,6), anchor="w")
        desc = ctk.CTkTextbox(dialog, height=100)
        desc.pack(padx=16, fill="both", expand=True)

        def save():
            name = name_entry.get().strip()
            description = desc.get("1.0", "end").strip()
            if not name:
                show_error("Lỗi", "Tên phòng ban không được rỗng")
                return
            ok = self.db.add_department(name, description)
            if ok:
                show_info("Thành công", "Đã thêm phòng ban mới")
                dialog.destroy()
                self.load_departments()
            else:
                show_error("Lỗi", "Tên phòng ban đã tồn tại")

        ctk.CTkButton(dialog, text="💾 Lưu", command=save, fg_color="#10b981").pack(padx=16, pady=12, fill="x")

    def open_edit_dialog(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        dept_id, name, desc_text = values[0], values[1], values[2] if len(values) > 2 else ""

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Sửa phòng ban")
        center_window(dialog, 500, 300)
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tên phòng ban:", font=ctk.CTkFont(size=13, weight="bold")).pack(padx=16, pady=(20,6), anchor="w")
        name_entry = ctk.CTkEntry(dialog, height=36)
        name_entry.insert(0, name)
        name_entry.pack(padx=16, fill="x")

        ctk.CTkLabel(dialog, text="Mô tả:", font=ctk.CTkFont(size=13, weight="bold")).pack(padx=16, pady=(12,6), anchor="w")
        desc = ctk.CTkTextbox(dialog, height=100)
        desc.insert("1.0", desc_text if desc_text else "")
        desc.pack(padx=16, fill="both", expand=True)

        def update():
            new_name = name_entry.get().strip()
            new_desc = desc.get("1.0", "end").strip()
            if not new_name:
                show_error("Lỗi", "Tên phòng ban không được rỗng")
                return
            self.db.update_department(dept_id, new_name, new_desc)
            show_info("Thành công", "Đã cập nhật phòng ban")
            dialog.destroy()
            self.load_departments()

        ctk.CTkButton(dialog, text="💾 Cập nhật", command=update, fg_color="#f59e0b").pack(padx=16, pady=12, fill="x")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        dept_id, name = values[0], values[1]
        if ask_confirm("Xác nhận", f"Bạn có chắc muốn xóa phòng ban '{name}'?"):
            try:
                self.db.delete_department(dept_id)
                show_info("Thành công", "Đã xóa phòng ban")
                self.load_departments()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa phòng ban: {e}")
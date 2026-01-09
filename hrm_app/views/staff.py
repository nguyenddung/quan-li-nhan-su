# hrm_app/views/staff.py
# Cập nhật: thêm tìm kiếm theo tên, menu chuột phải có "Xem hồ sơ" để mở dialog hiển thị hồ sơ của nhân viên
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from ..dialogs import center_window, show_info, show_error, ask_confirm
from .documents import DocumentsView

class StaffView:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        # DocumentsView instance để tái sử dụng chức năng quản lý tài liệu (mở dialog cho 1 nhân viên)
        self.docs_view = DocumentsView(app, db)

    def render(self):
        header = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0,8))

        # Search box (theo yêu cầu)
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True, padx=(0,12))

        ctk.CTkLabel(search_frame, text="Tìm theo tên:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0,8))
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Nhập tên cần tìm...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
        ctk.CTkButton(search_frame, text="🔎", width=40, command=self.on_search).pack(side="left")

        if self.app.is_admin:
            add_btn = ctk.CTkButton(header, text="➕ Thêm nhân viên", fg_color="#4f46e5", hover_color="#4338ca",
                                    command=self.open_add_dialog)
            add_btn.pack(side="right", padx=4)

        table_frame = ctk.CTkFrame(self.app.content_frame, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True, pady=(8,0))

        columns = ("ID","STT","Họ và tên","Vị trí","Điện thoại","Ngày sinh","Phòng ban")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("STT", width=60, anchor="center")
        self.tree.column("Họ và tên", width=220)
        self.tree.column("Vị trí", width=180)
        self.tree.column("Điện thoại", width=120, anchor="center")
        self.tree.column("Ngày sinh", width=120, anchor="center")
        self.tree.column("Phòng ban", width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y", pady=12, padx=(0,12))

        self.load_staffs()

        if self.app.is_admin:
            self.tree.bind("<Button-3>", self.on_right_click)
        else:
            # Nếu không phải admin vẫn cho phép xem hồ sơ (double click để xem hồ sơ)
            self.tree.bind("<Double-1>", self.on_double_click_view_docs)

    def load_staffs(self, query=None):
        """Load danh sách nhân viên; nếu query != None -> tìm theo tên"""
        self.tree.delete(*self.tree.get_children())
        if query:
            rows = self.db.search_staffs_by_name(query)
        else:
            rows = self.db.get_all_staffs()
        for r in rows:
            # r = (id, stt, full_name, position, phone, dob, dept_name)
            self.tree.insert("", "end", values=r)

    def on_search(self):
        q = self.search_entry.get().strip()
        self.load_staffs(query=q if q else None)

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="📄 Xem hồ sơ", command=self.open_view_documents_for_selected)
        menu.add_separator()
        menu.add_command(label="✏️ Sửa", command=self.open_edit_dialog)
        menu.add_command(label="🗑️ Xóa", command=self.delete_selected)
        menu.post(event.x_root, event.y_root)

    def on_double_click_view_docs(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item)['values']
        staff_id = values[0]
        staff_name = values[2]
        self.docs_view.open_staff_documents_dialog(staff_id, staff_name)

    def open_view_documents_for_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        staff_id = values[0]
        staff_name = values[2]
        self.docs_view.open_staff_documents_dialog(staff_id, staff_name)

    def open_add_dialog(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Thêm nhân viên mới")
        center_window(dialog, 600, 520)
        dialog.transient(self.app)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # STT
        ctk.CTkLabel(scroll, text="STT:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        stt_ent = ctk.CTkEntry(scroll, height=34); stt_ent.pack(fill="x")

        # Họ tên
        ctk.CTkLabel(scroll, text="Họ và tên:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        name_ent = ctk.CTkEntry(scroll, height=34); name_ent.pack(fill="x")

        # Ngày sinh
        ctk.CTkLabel(scroll, text="Ngày sinh (YYYY-MM-DD):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        dob_ent = ctk.CTkEntry(scroll, height=34); dob_ent.pack(fill="x")

        # Vị trí
        ctk.CTkLabel(scroll, text="Vị trí:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        pos_ent = ctk.CTkEntry(scroll, height=34); pos_ent.pack(fill="x")

        # Điện thoại
        ctk.CTkLabel(scroll, text="Điện thoại:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        phone_ent = ctk.CTkEntry(scroll, height=34); phone_ent.pack(fill="x")

        # Phòng ban (combo)
        ctk.CTkLabel(scroll, text="Phòng ban:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        depts = self.db.get_all_departments()
        dept_names = [d[1] for d in depts]
        dept_map = {d[1]: d[0] for d in depts}
        dept_combo = ctk.CTkComboBox(scroll, values=dept_names, height=34, state="readonly")
        if dept_names:
            dept_combo.set(dept_names[0])
        dept_combo.pack(fill="x", pady=(0,8))

        def save():
            stt = stt_ent.get().strip()
            name = name_ent.get().strip()
            dob = dob_ent.get().strip()
            pos = pos_ent.get().strip()
            phone = phone_ent.get().strip()
            dept = dept_combo.get()
            if not name:
                show_error("Lỗi", "Vui lòng nhập họ tên")
                return
            dept_id = dept_map.get(dept)
            self.db.add_staff(int(stt) if stt.isdigit() else None, name, dob if dob else None, pos, phone, dept_id)
            show_info("Thành công", "Đã thêm nhân viên")
            dialog.destroy()
            self.load_staffs()

        ctk.CTkButton(scroll, text="💾 Lưu nhân viên", command=save, fg_color="#10b981").pack(fill="x", pady=12)

    def open_edit_dialog(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        staff_id, stt, name, position, phone, dob, dept_name = values

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Sửa thông tin nhân viên")
        center_window(dialog, 600, 520)
        dialog.transient(self.app)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(scroll, text="STT:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        stt_ent = ctk.CTkEntry(scroll, height=34); stt_ent.insert(0, str(stt) if stt else ""); stt_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Họ và tên:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        name_ent = ctk.CTkEntry(scroll, height=34); name_ent.insert(0, name); name_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Ngày sinh (YYYY-MM-DD):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        dob_ent = ctk.CTkEntry(scroll, height=34); dob_ent.insert(0, dob if dob else ""); dob_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Vị trí:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        pos_ent = ctk.CTkEntry(scroll, height=34); pos_ent.insert(0, position if position else ""); pos_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Điện thoại:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        phone_ent = ctk.CTkEntry(scroll, height=34); phone_ent.insert(0, phone if phone else ""); phone_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Phòng ban:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        depts = self.db.get_all_departments()
        dept_names = [d[1] for d in depts]
        dept_map = {d[1]: d[0] for d in depts}
        dept_combo = ctk.CTkComboBox(scroll, values=dept_names, height=34, state="readonly")
        if dept_name in dept_names:
            dept_combo.set(dept_name)
        elif dept_names:
            dept_combo.set(dept_names[0])
        dept_combo.pack(fill="x", pady=(0,8))

        def update():
            new_stt = stt_ent.get().strip()
            new_name = name_ent.get().strip()
            new_dob = dob_ent.get().strip()
            new_pos = pos_ent.get().strip()
            new_phone = phone_ent.get().strip()
            new_dept = dept_combo.get()
            if not new_name:
                show_error("Lỗi", "Vui lòng nhập họ tên")
                return
            new_dept_id = dept_map.get(new_dept)
            self.db.update_staff(staff_id, int(new_stt) if new_stt.isdigit() else None, new_name, new_dob if new_dob else None, new_pos, new_phone, new_dept_id)
            show_info("Thành công", "Đã cập nhật nhân viên")
            dialog.destroy()
            self.load_staffs()

        ctk.CTkButton(scroll, text="💾 Cập nhật", command=update, fg_color="#f59e0b").pack(fill="x", pady=12)

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        staff_id, _, name = values[0], values[1], values[2]
        if ask_confirm("Xác nhận", f"Bạn có chắc muốn xóa nhân viên '{name}'?"):
            try:
                self.db.delete_staff(staff_id)
                show_info("Thành công", "Đã xóa nhân viên")
                self.load_staffs()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa nhân viên: {e}")
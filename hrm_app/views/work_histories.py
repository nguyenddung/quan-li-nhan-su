"""
work_histories.py
View quản lý Quá trình công tác (Work History)
- Hiển thị tất cả bản ghi (kèm tên nhân viên)
- Thêm / Sửa / Xóa bản ghi
- Tìm/filter theo nhân viên (combo)
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from ..dialogs import center_window, show_info, show_error, ask_confirm

class WorkHistoriesView:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def render(self):
        header = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0,10))

        # Filter theo nhân viên (combo) và nút reload
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.pack(side="left", fill="x", expand=True, padx=(0,12))

        ctk.CTkLabel(filter_frame, text="Lọc nhân viên:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0,8))
        staffs = self.db.get_all_staffs()
        staff_names = ["Tất cả"] + [f"{s[2]} (ID:{s[0]})" for s in staffs]
        self.staff_map = {f"{s[2]} (ID:{s[0]})": s[0] for s in staffs}
        self.staff_combo = ctk.CTkComboBox(filter_frame, values=staff_names, state="readonly", width=300)
        self.staff_combo.set("Tất cả")
        self.staff_combo.pack(side="left", padx=(0,8))

        ctk.CTkButton(filter_frame, text="🔁 Lọc", command=self.on_filter).pack(side="left")

        if self.app.is_admin:
            add_btn = ctk.CTkButton(header, text="➕ Thêm quá trình", fg_color="#4f46e5", command=self.open_add_dialog)
            add_btn.pack(side="right", padx=4)

        # Table
        table_frame = ctk.CTkFrame(self.app.content_frame, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True)

        cols = ("ID", "Nhân viên", "Số quyết định", "Ngày quyết định", "Các vị trí công tác", "Giữ chức vụ", "Công tác tại CQ", "Ghi chú")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Nhân viên", width=220)
        self.tree.column("Số quyết định", width=140)
        self.tree.column("Ngày quyết định", width=120, anchor="center")
        self.tree.column("Các vị trí công tác", width=220)
        self.tree.column("Giữ chức vụ", width=120, anchor="center")
        self.tree.column("Công tác tại CQ", width=120, anchor="center")
        self.tree.column("Ghi chú", width=220)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y", pady=12, padx=(0,12))

        self.load_all_histories()

        if self.app.is_admin:
            self.tree.bind("<Button-3>", self.on_right_click)

    def load_all_histories(self):
        self.tree.delete(*self.tree.get_children())
        rows = self.db.get_all_work_histories()
        for r in rows:
            # r = (wh.id, staff_name, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu, staff_id)
            display = (r[0], r[1] or "-", r[2] or "-", r[3] or "-", r[4] or "-", r[5] or "-", r[6] or "-", r[7] or "")
            self.tree.insert("", "end", values=display)

    def on_filter(self):
        sel = self.staff_combo.get()
        if sel == "Tất cả":
            self.load_all_histories()
            return
        staff_id = self.staff_map.get(sel)
        if staff_id is None:
            self.load_all_histories()
            return
        rows = self.db.get_work_histories_by_staff(staff_id)
        self.tree.delete(*self.tree.get_children())
        # rows: (id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu)
        # Need staff name too:
        staff_name = sel.split(" (ID:")[0]
        for r in rows:
            display = (r[0], staff_name, r[1] or "-", r[2] or "-", r[3] or "-", r[4] or "-", r[5] or "-", r[6] or "")
            self.tree.insert("", "end", values=display)

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="✏️ Sửa", command=self.open_edit_dialog)
        menu.add_command(label="🗑️ Xóa", command=self.delete_selected)
        menu.post(event.x_root, event.y_root)

    def open_add_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Thêm quá trình công tác")
        center_window(dlg, 700, 520)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        # Chọn nhân viên
        ctk.CTkLabel(frm, text="Chọn nhân viên:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(4,6))
        staffs = self.db.get_all_staffs()
        staff_map = {f"{s[2]} (ID:{s[0]})": s[0] for s in staffs}
        staff_combo = ctk.CTkComboBox(frm, values=list(staff_map.keys()), state="readonly")
        if staff_map:
            staff_combo.set(list(staff_map.keys())[0])
        staff_combo.pack(fill="x", pady=(0,8))

        ctk.CTkLabel(frm, text="Số quyết định:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        decision_ent = ctk.CTkEntry(frm); decision_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Ngày quyết định:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        ngay_ent = ctk.CTkEntry(frm); ngay_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Các vị trí công tác:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        vitri_ent = ctk.CTkEntry(frm); vitri_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Giữ chức vụ:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        giu_ent = ctk.CTkEntry(frm); giu_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Công tác tại Cơ quan:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        cq_ent = ctk.CTkEntry(frm); cq_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Ghi chú:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        note_txt = ctk.CTkTextbox(frm, height=80); note_txt.pack(fill="x")

        def save():
            staff_key = staff_combo.get()
            if not staff_key:
                show_error("Lỗi", "Vui lòng chọn nhân viên")
                return
            staff_id = staff_map[staff_key]
            decision_no = decision_ent.get().strip()
            ngay = ngay_ent.get().strip()
            vitri = vitri_ent.get().strip()
            giu = giu_ent.get().strip()
            cq = cq_ent.get().strip()
            ghi = note_txt.get("1.0", "end").strip()
            try:
                self.db.add_work_history(staff_id, decision_no, ngay, vitri, giu, cq, ghi)
                show_info("Thành công", "Đã thêm quá trình công tác")
                dlg.destroy()
                self.load_all_histories()
            except Exception as e:
                show_error("Lỗi", f"Không thể thêm: {e}")

        ctk.CTkButton(frm, text="💾 Lưu", command=save, fg_color="#10b981").pack(fill="x", pady=8)

    def open_edit_dialog(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        # values = (id, staff_name, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu)
        wh_id = values[0]
        staff_name = values[1]

        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Sửa quá trình công tác")
        center_window(dlg, 700, 520)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(frm, text=f"Nhân viên: {staff_name}", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(4,8))
        ctk.CTkLabel(frm, text="Số quyết định:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        decision_ent = ctk.CTkEntry(frm); decision_ent.insert(0, values[2] or ""); decision_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Ngày quyết định:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        ngay_ent = ctk.CTkEntry(frm); ngay_ent.insert(0, values[3] or ""); ngay_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Các vị trí công tác:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        vitri_ent = ctk.CTkEntry(frm); vitri_ent.insert(0, values[4] or ""); vitri_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Giữ chức vụ:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        giu_ent = ctk.CTkEntry(frm); giu_ent.insert(0, values[5] or ""); giu_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Công tác tại Cơ quan:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        cq_ent = ctk.CTkEntry(frm); cq_ent.insert(0, values[6] or ""); cq_ent.pack(fill="x")
        ctk.CTkLabel(frm, text="Ghi chú:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(6,4))
        note_txt = ctk.CTkTextbox(frm, height=80); note_txt.insert("1.0", values[7] or ""); note_txt.pack(fill="x")

        def save():
            decision_no = decision_ent.get().strip()
            ngay = ngay_ent.get().strip()
            vitri = vitri_ent.get().strip()
            giu = giu_ent.get().strip()
            cq = cq_ent.get().strip()
            ghi = note_txt.get("1.0", "end").strip()
            try:
                self.db.update_work_history(wh_id, decision_no, ngay, vitri, giu, cq, ghi)
                show_info("Thành công", "Đã cập nhật quá trình công tác")
                dlg.destroy()
                self.load_all_histories()
            except Exception as e:
                show_error("Lỗi", f"Không thể cập nhật: {e}")

        ctk.CTkButton(frm, text="💾 Lưu", command=save, fg_color="#f59e0b").pack(fill="x", pady=8)

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        wh_id = values[0]
        if ask_confirm("Xác nhận", "Bạn có chắc muốn xóa bản ghi quá trình công tác này?"):
            try:
                self.db.delete_work_history(wh_id)
                show_info("Thành công", "Đã xóa bản ghi")
                self.load_all_histories()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa: {e}")
# hrm_app/views/documents.py
# Cập nh���t: thêm chức năng SỬA và XÓA tài liệu trong dialog "Hồ sơ của nhân viên"
import customtkinter as ctk
from tkinter import ttk, Menu
from ..dialogs import center_window, show_info, show_error, ask_confirm

class DocumentsView:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def render(self):
        header = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0,14))
        if self.app.is_admin:
            add_btn = ctk.CTkButton(header, text="➕ Thêm tài liệu", fg_color="#4f46e5", hover_color="#4338ca", command=self.open_add_dialog)
            add_btn.pack(side="right", padx=4)

        table_frame = ctk.CTkFrame(self.app.content_frame, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID","Nhân viên","Loại hồ sơ","Số ký hiệu","Ngày tháng","File")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        for c in columns:
            self.tree.heading(c, text=c)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nhân viên", width=220)
        self.tree.column("Loại hồ sơ", width=200)
        self.tree.column("Số ký hiệu", width=150)
        self.tree.column("Ngày tháng", width=120, anchor="center")
        self.tree.column("File", width=260)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y", pady=12, padx=(0,12))

        self.load_documents()

    def load_documents(self):
        try:
            self.tree.delete(*self.tree.get_children())
        except Exception:
            pass
        docs = self.db.get_all_documents()
        for d in docs:
            # d = (id, staff_full_name, loai_ho_so, so_va_ky_hieu, ngay_thang, file_url)
            self.tree.insert("", "end", values=d)

    def open_add_dialog(self, preset_staff_id=None):
        """
        Mở dialog thêm tài liệu.
        Nếu preset_staff_id != None -> preselect nhân viên đó
        """
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Thêm tài liệu mới")
        center_window(dialog, 700, 650)
        dialog.transient(self.app)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Nhân viên
        ctk.CTkLabel(scroll, text="Chọn nhân viên:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        staffs = self.db.get_all_staffs()
        staff_names = [f"{s[2]} (ID: {s[0]})" for s in staffs]
        staff_map = {f"{s[2]} (ID: {s[0]})": s[0] for s in staffs}
        staff_combo = ctk.CTkComboBox(scroll, values=staff_names, state="readonly")
        if staff_names:
            # nếu có preset_staff_id thì set tương ứng
            if preset_staff_id:
                for k, v in staff_map.items():
                    if v == preset_staff_id:
                        staff_combo.set(k)
                        break
                else:
                    staff_combo.set(staff_names[0])
            else:
                staff_combo.set(staff_names[0])
        staff_combo.pack(fill="x", pady=(0,8))

        ctk.CTkLabel(scroll, text="Loại hồ sơ:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        loai_ent = ctk.CTkEntry(scroll); loai_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Số và ký hiệu:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        so_ent = ctk.CTkEntry(scroll); so_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Ngày tháng:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        ngay_ent = ctk.CTkEntry(scroll); ngay_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Trích yếu nội dung:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        trichyeu = ctk.CTkTextbox(scroll, height=90); trichyeu.pack(fill="x")

        ctk.CTkLabel(scroll, text="Số tờ:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        soto_ent = ctk.CTkEntry(scroll); soto_ent.pack(fill="x")

        ctk.CTkLabel(scroll, text="Ghi chú:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        ghi_chu = ctk.CTkTextbox(scroll, height=80); ghi_chu.pack(fill="x")

        ctk.CTkLabel(scroll, text="Đường dẫn file:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
        file_ent = ctk.CTkEntry(scroll); file_ent.pack(fill="x")

        def save():
            staff_key = staff_combo.get()
            if not staff_key:
                show_error("Lỗi", "Vui lòng chọn nhân viên")
                return
            staff_id = staff_map.get(staff_key)
            loai = loai_ent.get().strip()
            so = so_ent.get().strip()
            ngay = ngay_ent.get().strip()
            ten_loai = trichyeu.get("1.0","end").strip()
            soto = soto_ent.get().strip()
            ghi = ghi_chu.get("1.0","end").strip()
            file_url = file_ent.get().strip()
            self.db.add_document(staff_id, loai, so, ngay, ten_loai, int(soto) if soto.isdigit() else None, ghi, file_url)
            show_info("Thành công", "Đã thêm tài liệu")
            dialog.destroy()
            # nếu đang ở view documents chính refresh
            try:
                self.load_documents()
            except:
                pass

        ctk.CTkButton(scroll, text="💾 Lưu tài liệu", command=save, fg_color="#10b981").pack(fill="x", pady=12)

    def open_staff_documents_dialog(self, staff_id, staff_name):
        """Mở dialog hiển thị toàn bộ hồ sơ của 1 nhân viên; có thể thêm tài liệu cho nhân viên này,
           sửa hoặc xóa tài liệu nếu is_admin=True"""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Hồ sơ của {staff_name}")
        center_window(dialog, 900, 600)
        dialog.transient(self.app)
        dialog.grab_set()

        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", pady=(8,8))

        if self.app.is_admin:
            ctk.CTkButton(header, text="➕ Thêm tài liệu cho nhân viên này", fg_color="#4f46e5",
                          command=lambda: self.open_add_dialog(preset_staff_id=staff_id)).pack(side="right", padx=8)

        table_frame = ctk.CTkFrame(dialog, fg_color="white", corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=12, pady=12)

        cols = ("ID","Loại hồ sơ","Số ký hiệu","Ngày tháng","Trích yếu","Số tờ","Ghi chú","File","Ngày tạo")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=50, anchor="center")
        tree.column("Loại hồ sơ", width=140)
        tree.column("Số ký hiệu", width=140)
        tree.column("Ngày tháng", width=120, anchor="center")
        tree.column("Trích yếu", width=260)
        tree.column("Số tờ", width=80, anchor="center")
        tree.column("Ghi chú", width=180)
        tree.column("File", width=170)
        tree.column("Ngày tạo", width=150)

        tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Load documents for staff
        def load_staff_docs():
            tree.delete(*tree.get_children())
            docs = self.db.get_documents_by_staff(staff_id)
            for d in docs:
                # d = (id, loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai_trich_yeu_noi_dung, so_to, ghi_chu, file_url, created_at)
                tree.insert("", "end", values=d)

        load_staff_docs()

        # Context menu for each document (edit / delete)
        if self.app.is_admin:
            def on_right_click(event):
                item = tree.identify_row(event.y)
                if not item:
                    return
                tree.selection_set(item)
                menu = Menu(dialog, tearoff=0)
                menu.add_command(label="✏️ Sửa", command=lambda: open_edit_dialog_for_selected())
                menu.add_command(label="🗑️ Xóa", command=lambda: delete_selected())
                menu.post(event.x_root, event.y_root)

            tree.bind("<Button-3>", on_right_click)

        def open_edit_dialog_for_selected():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0])['values']
            # values corresponds to (id, loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai_trich_yeu_noi_dung, so_to, ghi_chu, file_url, created_at)
            doc_id = values[0]
            loai = values[1] or ""
            so = values[2] or ""
            ngay = values[3] or ""
            ten_loai = values[4] or ""
            so_to = values[5] or ""
            ghi_chu = values[6] or ""
            file_url = values[7] or ""

            edit = ctk.CTkToplevel(dialog)
            edit.title("Sửa thông tin tài liệu")
            center_window(edit, 700, 620)
            edit.transient(dialog)
            edit.grab_set()

            scroll = ctk.CTkScrollableFrame(edit)
            scroll.pack(fill="both", expand=True, padx=12, pady=12)

            # Không cho đổi nhân viên ở đây (document thuộc staff đang xem)
            ctk.CTkLabel(scroll, text=f"Nhân viên: {staff_name}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4,8))

            ctk.CTkLabel(scroll, text="Loại hồ sơ:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            loai_ent = ctk.CTkEntry(scroll); loai_ent.insert(0, loai); loai_ent.pack(fill="x")

            ctk.CTkLabel(scroll, text="Số và ký hiệu:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            so_ent = ctk.CTkEntry(scroll); so_ent.insert(0, so); so_ent.pack(fill="x")

            ctk.CTkLabel(scroll, text="Ngày tháng:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            ngay_ent = ctk.CTkEntry(scroll); ngay_ent.insert(0, ngay); ngay_ent.pack(fill="x")

            ctk.CTkLabel(scroll, text="Trích yếu nội dung:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            trichyeu = ctk.CTkTextbox(scroll, height=90); trichyeu.insert("1.0", ten_loai); trichyeu.pack(fill="x")

            ctk.CTkLabel(scroll, text="Số tờ:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            soto_ent = ctk.CTkEntry(scroll); soto_ent.insert(0, str(so_to) if so_to is not None else ""); soto_ent.pack(fill="x")

            ctk.CTkLabel(scroll, text="Ghi chú:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            ghi_chu_ent = ctk.CTkTextbox(scroll, height=80); ghi_chu_ent.insert("1.0", ghi_chu); ghi_chu_ent.pack(fill="x")

            ctk.CTkLabel(scroll, text="Đường dẫn file:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8,4))
            file_ent = ctk.CTkEntry(scroll); file_ent.insert(0, file_url); file_ent.pack(fill="x")

            def save_edit():
                new_loai = loai_ent.get().strip()
                new_so = so_ent.get().strip()
                new_ngay = ngay_ent.get().strip()
                new_ten_loai = trichyeu.get("1.0","end").strip()
                new_soto = soto_ent.get().strip()
                new_ghi = ghi_chu_ent.get("1.0","end").strip()
                new_file = file_ent.get().strip()
                try:
                    self.db.update_document(doc_id, new_loai, new_so, new_ngay, new_ten_loai, int(new_soto) if new_soto.isdigit() else None, new_ghi, new_file)
                    show_info("Thành công", "Đã cập nhật tài liệu")
                    edit.destroy()
                    load_staff_docs()
                except Exception as e:
                    show_error("Lỗi", f"Không thể cập nhật tài liệu: {e}")

            ctk.CTkButton(scroll, text="💾 Lưu thay đổi", command=save_edit, fg_color="#f59e0b").pack(fill="x", pady=12)

        def delete_selected():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0])['values']
            doc_id = values[0]
            if ask_confirm("Xác nhận", "Bạn có chắc muốn xóa tài liệu này?"):
                try:
                    self.db.delete_document(doc_id)
                    show_info("Thành công", "Đã xóa tài liệu")
                    load_staff_docs()
                except Exception as e:
                    show_error("Lỗi", f"Không thể xóa tài liệu: {e}")
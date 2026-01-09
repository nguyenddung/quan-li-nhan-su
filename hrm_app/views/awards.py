"""
hrm_app/views/awards.py
Giao diện quản lý chuẩn cho Khen thưởng theo model của bạn.

Các phần trong UI:
- Tab/section: Năm | Danh hiệu | Cơ quan | Đợt quyết định | Phân bổ (Cá nhân / Tập thể)
- CRUD cơ bản với dialog thêm/sửa
- Phân bổ: chọn đợt -> chọn nhân viên hoặc phòng ban -> add staff_award / department_award
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from ..dialogs import center_window, show_info, show_error, ask_confirm

class AwardsView:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def render(self):
        # Container chính
        container = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Sử dụng Paned layout: trên là controls, dưới là lists
        top_frame = ctk.CTkFrame(container, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0,12))

        # Buttons nhanh: quản lý từng phần
        btn_years = ctk.CTkButton(top_frame, text="📅 Năm khen thưởng", command=self.open_years_dialog, fg_color="#3b82f6")
        btn_titles = ctk.CTkButton(top_frame, text="🏅 Danh hiệu", command=self.open_titles_dialog, fg_color="#8b5cf6")
        btn_auth = ctk.CTkButton(top_frame, text="🏛️ Cơ quan", command=self.open_authorities_dialog, fg_color="#06b6d4")
        btn_batches = ctk.CTkButton(top_frame, text="🗂️ Đợt / Quyết định", command=self.open_batches_dialog, fg_color="#f59e0b")
        btn_assign = ctk.CTkButton(top_frame, text="🔁 Phân bổ khen thưởng", command=self.open_assign_dialog, fg_color="#10b981")

        for b in (btn_years, btn_titles, btn_auth, btn_batches, btn_assign):
            b.pack(side="left", padx=8)

        # Phần danh sách tổng quan (batches + recent assignments)
        list_frame = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        list_frame.pack(fill="both", expand=True)

        # Left: danh sách batches
        left = ctk.CTkFrame(list_frame, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(left, text="Đợt / Quyết định khen thưởng (mới nhất)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(4,8))
        cols = ("ID","Năm","Danh hiệu","Cấp","Cơ quan","Số quyết định","Ngày","Ghi chú")
        self.tree_batches = ttk.Treeview(left, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree_batches.heading(c, text=c)
        self.tree_batches.column("ID", width=50, anchor="center")
        self.tree_batches.column("Năm", width=80)
        self.tree_batches.column("Danh hiệu", width=200)
        self.tree_batches.column("Cấp", width=100)
        self.tree_batches.column("Cơ quan", width=180)
        self.tree_batches.column("Số quyết định", width=120)
        self.tree_batches.column("Ngày", width=120)
        self.tree_batches.column("Ghi chú", width=240)

        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree_batches.yview)
        self.tree_batches.configure(yscrollcommand=sb.set)
        self.tree_batches.pack(side="left", fill="both", expand=True, padx=(0,0))
        sb.pack(side="right", fill="y", padx=(0,8))

        # Right: recent assignments (cá nhân + tập thể)
        right = ctk.CTkFrame(list_frame, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(right, text="Khen thưởng cho cá nhân (mới nhất)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(4,8))
        self.tree_staff_awards = ttk.Treeview(right, columns=("ID","Nhân viên","Năm","Danh hiệu","Cơ quan","Quyết định"), show="headings", height=6)
        for h,cw in [("ID",39),("Nhân viên",180),("Năm",80),("Danh hiệu",150),("Cơ quan",140),("Quyết định",120)]:
            self.tree_staff_awards.heading(h, text=h)
            self.tree_staff_awards.column(h, width=cw)
        sb2 = ttk.Scrollbar(right, orient="vertical", command=self.tree_staff_awards.yview)
        self.tree_staff_awards.configure(yscrollcommand=sb2.set)
        self.tree_staff_awards.pack(fill="both", padx=(0,0))
        sb2.pack(side="right", fill="y", padx=(0,8))

        ctk.CTkLabel(right, text="Khen thưởng cho tập thể (mới nhất)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(12,8))
        self.tree_dept_awards = ttk.Treeview(right, columns=("ID","Phòng ban","Năm","Danh hiệu","Quyết định"), show="headings", height=6)
        for h,cw in [("ID",50),("Phòng ban",180),("Năm",80),("Danh hiệu",150),("Quyết định",120)]:
            self.tree_dept_awards.heading(h, text=h)
            self.tree_dept_awards.column(h, width=cw)
        sb3 = ttk.Scrollbar(right, orient="vertical", command=self.tree_dept_awards.yview)
        self.tree_dept_awards.configure(yscrollcommand=sb3.set)
        self.tree_dept_awards.pack(fill="both", padx=(0,0))
        sb3.pack(side="right", fill="y", padx=(0,8))

        # Load initial data
        self.load_batches()
        self.load_recent_assignments()

        # Context menus: cho phép xóa batch / assignment bằng right click (nếu admin)
        if self.app.is_admin:
            self.tree_batches.bind("<Button-3>", self.on_batch_right_click)
            self.tree_staff_awards.bind("<Button-3>", self.on_staff_award_right_click)
            self.tree_dept_awards.bind("<Button-3>", self.on_dept_award_right_click)

    # -------------------------
    # Loaders
    # -------------------------
    def load_batches(self):
        for i in self.tree_batches.get_children():
            self.tree_batches.delete(i)
        rows = self.db.get_all_award_batches()
        for r in rows:
            # r = (ab.id, ay.year, at.name, at.level, aa.name, ab.decision_no, ab.decision_date, ab.note, award_year_id, award_title_id, authority_id)
            display = (r[0], r[1], r[2], r[3], r[4] or "-", r[5] or "-", r[6] or "-", r[7] or "")
            self.tree_batches.insert("", "end", values=display)

    def load_recent_assignments(self):
        # staff awards (recent)
        for i in self.tree_staff_awards.get_children():
            self.tree_staff_awards.delete(i)
        conn_rows = []
        # Simple query: lấy staff_awards mới nhất (join batch/title/year/authority)
        # We reuse get_staff_awards_by_staff for a few staff or implement a join here:
        # For simplicity: lấy top 10 staff_awards via raw query
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT sa.id, s.full_name, ay.year, at.name, aa.name, ab.decision_no
            FROM staff_awards sa
            JOIN staffs s ON sa.staff_id = s.id
            JOIN award_batches ab ON sa.award_batch_id = ab.id
            JOIN award_titles at ON ab.award_title_id = at.id
            JOIN award_years ay ON ab.award_year_id = ay.id
            LEFT JOIN award_authorities aa ON ab.authority_id = aa.id
            ORDER BY ab.decision_date DESC
            LIMIT 10
        ''')
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            self.tree_staff_awards.insert("", "end", values=r)

        # department awards
        for i in self.tree_dept_awards.get_children():
            self.tree_dept_awards.delete(i)
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT da.id, d.name, ay.year, at.name, ab.decision_no
            FROM department_awards da
            JOIN departments d ON da.department_id = d.id
            JOIN award_batches ab ON da.award_batch_id = ab.id
            JOIN award_titles at ON ab.award_title_id = at.id
            JOIN award_years ay ON ab.award_year_id = ay.id
            ORDER BY ab.decision_date DESC
            LIMIT 10
        ''')
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            self.tree_dept_awards.insert("", "end", values=r)

    # -------------------------
    # Context menu callbacks
    # -------------------------
    def on_batch_right_click(self, event):
        item = self.tree_batches.identify_row(event.y)
        if not item:
            return
        self.tree_batches.selection_set(item)
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="✏️ Sửa đợt", command=self.open_edit_batch_dialog)
        menu.add_command(label="🗑️ Xóa đợt", command=self.delete_selected_batch)
        menu.post(event.x_root, event.y_root)

    def on_staff_award_right_click(self, event):
        item = self.tree_staff_awards.identify_row(event.y)
        if not item:
            return
        self.tree_staff_awards.selection_set(item)
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="🗑️ Xóa khen thưởng", command=self.delete_selected_staff_award)
        menu.post(event.x_root, event.y_root)

    def on_dept_award_right_click(self, event):
        item = self.tree_dept_awards.identify_row(event.y)
        if not item:
            return
        self.tree_dept_awards.selection_set(item)
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="🗑️ Xóa khen thưởng", command=self.delete_selected_dept_award)
        menu.post(event.x_root, event.y_root)

    # -------------------------
    # Batch dialogs (add / edit)
    # -------------------------
    def open_batches_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Quản lý Đợt / Quyết định khen thưởng")
        center_window(dlg, 900, 600)
        dlg.transient(self.app)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        # Left: list
        left = ctk.CTkFrame(frame)
        left.pack(side="left", fill="both", expand=True, padx=(0,8))
        cols = ("ID","Năm","Danh hiệu","Cấp","Cơ quan","Số quyết định","Ngày","Ghi chú")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Right: controls
        right = ctk.CTkFrame(frame)
        right.pack(side="right", fill="y", padx=(8,0))

        ctk.CTkButton(right, text="➕ Thêm đợt", command=lambda: self.open_add_batch_dialog(parent=dlg, refresh_cb=lambda: self._refresh_tree(tree))).pack(fill="x", pady=6)
        ctk.CTkButton(right, text="🔁 Tải lại", command=lambda: self._refresh_tree(tree)).pack(fill="x", pady=6)

        # load into tree
        rows = self.db.get_all_award_batches()
        for r in rows:
            display = (r[0], r[1], r[2], r[3], r[4] or "-", r[5] or "-", r[6] or "-", r[7] or "")
            tree.insert("", "end", values=display)

        # right-click edit/delete
        if self.app.is_admin:
            def on_right(event):
                it = tree.identify_row(event.y)
                if not it:
                    return
                tree.selection_set(it)
                menu = tk.Menu(dlg, tearoff=0)
                menu.add_command(label="✏️ Sửa", command=lambda: self._open_edit_batch_from_tree(tree))
                menu.add_command(label="🗑️ Xóa", command=lambda: self._delete_batch_from_tree(tree, refresh_cb=lambda: self._refresh_tree(tree)))
                menu.post(event.x_root, event.y_root)
            tree.bind("<Button-3>", on_right)

    def _refresh_tree(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        rows = self.db.get_all_award_batches()
        for r in rows:
            display = (r[0], r[1], r[2], r[3], r[4] or "-", r[5] or "-", r[6] or "-", r[7] or "")
            tree.insert("", "end", values=display)

    def open_add_batch_dialog(self, parent=None, refresh_cb=None):
        dlg = ctk.CTkToplevel(parent or self.app)
        dlg.title("Thêm đợt khen thưởng")
        center_window(dlg, 560, 420)
        dlg.transient(parent or self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(frm, text="Năm:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        years = self.db.get_all_award_years()
        year_map = {str(y[1]): y[0] for y in years}
        year_combo = ctk.CTkComboBox(frm, values=[str(y[1]) for y in years], state="readonly")
        if years:
            year_combo.set(str(years[0][1]))
        year_combo.pack(fill="x", pady=6)

        ctk.CTkLabel(frm, text="Danh hiệu:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        titles = self.db.get_all_award_titles()
        title_map = {t[1]: t[0] for t in titles}
        title_combo = ctk.CTkComboBox(frm, values=[t[1] for t in titles], state="readonly")
        if titles:
            title_combo.set(titles[0][1])
        title_combo.pack(fill="x", pady=6)

        ctk.CTkLabel(frm, text="Cơ quan ban hành (tùy chọn):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        auths = self.db.get_all_award_authorities()
        auth_map = {a[1]: a[0] for a in auths}
        auth_combo = ctk.CTkComboBox(frm, values=[a[1] for a in auths], state="readonly")
        if auths:
            auth_combo.set(auths[0][1])
        auth_combo.pack(fill="x", pady=6)

        ctk.CTkLabel(frm, text="Số quyết định:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        dec_ent = ctk.CTkEntry(frm); dec_ent.pack(fill="x", pady=6)

        ctk.CTkLabel(frm, text="Ngày quyết định (YYYY-MM-DD):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        date_ent = ctk.CTkEntry(frm); date_ent.pack(fill="x", pady=6)

        ctk.CTkLabel(frm, text="Ghi chú:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        note_txt = ctk.CTkTextbox(frm, height=80); note_txt.pack(fill="both", pady=6)

        def save():
            if not year_combo.get() or not title_combo.get():
                show_error("Lỗi", "Cần chọn năm và danh hiệu")
                return
            award_year_id = year_map.get(year_combo.get())
            award_title_id = title_map.get(title_combo.get())
            authority_id = auth_map.get(auth_combo.get()) if auth_combo.get() else None
            decision_no = dec_ent.get().strip()
            decision_date = date_ent.get().strip()
            note = note_txt.get("1.0","end").strip()
            try:
                self.db.add_award_batch(award_year_id, award_title_id, authority_id, decision_no, decision_date, note)
                show_info("Thành công", "Đã tạo đợt khen thưởng")
                dlg.destroy()
                if refresh_cb:
                    refresh_cb()
                else:
                    self.load_batches()
            except Exception as e:
                show_error("Lỗi", f"Không thể thêm đợt: {e}")

        ctk.CTkButton(frm, text="💾 Lưu đợt", command=save, fg_color="#10b981").pack(fill="x", pady=6)

    def _open_edit_batch_from_tree(self, tree):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0])['values']
        batch_id = vals[0]
        # get full batch info
        # reuse get_all_award_batches and find by id
        rows = self.db.get_all_award_batches()
        batch = next((r for r in rows if r[0] == batch_id), None)
        if batch:
            self.open_edit_batch_dialog(batch=batch)

    def open_edit_batch_dialog(self, batch=None):
        if batch is None:
            sel = self.tree_batches.selection()
            if not sel:
                return
            vals = self.tree_batches.item(sel[0])['values']
            batch_id = vals[0]
            rows = self.db.get_all_award_batches()
            batch = next((r for r in rows if r[0] == batch_id), None)
        if batch is None:
            show_error("Lỗi", "Không tìm thấy đợt")
            return
        # batch tuple: (id, year, title_name, level, authority_name, decision_no, decision_date, note, year_id, title_id, authority_id)
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Sửa đợt khen thưởng")
        center_window(dlg, 560, 420)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg); frm.pack(fill="both", expand=True, padx=12, pady=12)
        years = self.db.get_all_award_years(); year_map = {str(y[1]): y[0] for y in years}
        year_combo = ctk.CTkComboBox(frm, values=[str(y[1]) for y in years], state="readonly"); year_combo.set(str(batch[1])); year_combo.pack(fill="x", pady=6)
        titles = self.db.get_all_award_titles(); title_map = {t[1]: t[0] for t in titles}
        title_combo = ctk.CTkComboBox(frm, values=[t[1] for t in titles], state="readonly"); title_combo.set(batch[2]); title_combo.pack(fill="x", pady=6)
        auths = self.db.get_all_award_authorities(); auth_map = {a[1]: a[0] for a in auths}
        auth_combo = ctk.CTkComboBox(frm, values=[a[1] for a in auths], state="readonly")
        if batch[4]:
            auth_combo.set(batch[4])
        elif auths:
            auth_combo.set(auths[0][1])
        auth_combo.pack(fill="x", pady=6)
        dec_ent = ctk.CTkEntry(frm); dec_ent.insert(0, batch[5] or ""); dec_ent.pack(fill="x", pady=6)
        date_ent = ctk.CTkEntry(frm); date_ent.insert(0, batch[6] or ""); date_ent.pack(fill="x", pady=6)
        note_txt = ctk.CTkTextbox(frm, height=80); note_txt.insert("1.0", batch[7] or ""); note_txt.pack(fill="both", pady=6)

        def save():
            award_year_id = year_map.get(year_combo.get())
            award_title_id = title_map.get(title_combo.get())
            authority_id = auth_map.get(auth_combo.get()) if auth_combo.get() else None
            decision_no = dec_ent.get().strip()
            decision_date = date_ent.get().strip()
            note = note_txt.get("1.0","end").strip()
            try:
                self.db.update_award_batch(batch[0], award_year_id, award_title_id, authority_id, decision_no, decision_date, note)
                show_info("Thành công", "Đã cập nhật đợt")
                dlg.destroy()
                self.load_batches()
            except Exception as e:
                show_error("Lỗi", f"Không thể cập nhật: {e}")

        ctk.CTkButton(frm, text="💾 Lưu thay đổi", command=save, fg_color="#f59e0b").pack(fill="x", pady=6)

    def _delete_batch_from_tree(self, tree, refresh_cb=None):
        sel = tree.selection()
        if not sel:
            return
        batch_id = tree.item(sel[0])['values'][0]
        if ask_confirm("Xác nhận", "Bạn có muốn xóa đợt khen thưởng này? (Hành động sẽ xóa cả khen thưởng liên quan)"):
            try:
                self.db.delete_award_batch(batch_id)
                show_info("Thành công", "Đã xóa đợt")
                if refresh_cb:
                    refresh_cb()
                else:
                    self.load_batches()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa: {e}")

    def delete_selected_batch(self):
        sel = self.tree_batches.selection()
        if not sel:
            return
        batch_id = self.tree_batches.item(sel[0])['values'][0]
        if ask_confirm("Xác nhận", "Bạn có muốn xóa đợt khen thưởng này?"):
            try:
                self.db.delete_award_batch(batch_id)
                show_info("Thành công", "Đã xóa đợt")
                self.load_batches()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa: {e}")

    # -------------------------
    # Assign dialog (khen cho cá nhân / phòng ban)
    # -------------------------
    def open_assign_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Phân bổ khen thưởng (Cá nhân / Tập thể)")
        center_window(dlg, 820, 520)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg); frm.pack(fill="both", expand=True, padx=12, pady=12)

        # Left: chọn đợt
        ctk.CTkLabel(frm, text="Chọn đợt/khen thưởng:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        batches = self.db.get_all_award_batches()
        batch_map = {f"[{r[1]}] {r[2]} ({r[5] or ''})": r[0] for r in batches}
        batch_combo = ctk.CTkComboBox(frm, values=list(batch_map.keys()), state="readonly", width=600)
        if batches:
            batch_combo.set(list(batch_map.keys())[0])
        batch_combo.pack(fill="x", pady=6)

        # Mid: chọn staff -> add staff_award
        ctk.CTkLabel(frm, text="Phân cho nhân viên (cá nhân):", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(12,4))
        staffs = self.db.get_all_staffs()
        staff_map = {f"{s[2]} (ID:{s[0]})": s[0] for s in staffs}
        staff_combo = ctk.CTkComboBox(frm, values=list(staff_map.keys()), state="readonly")
        if staffs:
            staff_combo.set(list(staff_map.keys())[0])
        staff_combo.pack(fill="x", pady=6)
        note_staff = ctk.CTkEntry(frm, placeholder_text="Ghi chú (tùy chọn)")
        note_staff.pack(fill="x", pady=6)

        def add_staff_award():
            if not batch_combo.get() or not staff_combo.get():
                show_error("Lỗi", "Vui lòng chọn đợt và nhân viên")
                return
            batch_id = batch_map.get(batch_combo.get())
            staff_id = staff_map.get(staff_combo.get())
            self.db.add_staff_award(staff_id, batch_id, note_staff.get().strip())
            show_info("Thành công", "Đã phân khen thưởng cho nhân viên")
            self.load_recent_assignments()

        ctk.CTkButton(frm, text="➕ Phân cho nhân viên", command=add_staff_award, fg_color="#10b981").pack(fill="x", pady=6)

        # Right: chọn department -> add department_award
        ctk.CTkLabel(frm, text="Phân cho phòng ban (tập thể):", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(12,4))
        depts = self.db.get_all_departments()
        dept_map = {f"{d[1]} (ID:{d[0]})": d[0] for d in depts}
        dept_combo = ctk.CTkComboBox(frm, values=list(dept_map.keys()), state="readonly")
        if depts:
            dept_combo.set(list(dept_map.keys())[0])
        dept_combo.pack(fill="x", pady=6)
        note_dept = ctk.CTkEntry(frm, placeholder_text="Ghi chú (tùy chọn)")
        note_dept.pack(fill="x", pady=6)

        def add_dept_award():
            if not batch_combo.get() or not dept_combo.get():
                show_error("Lỗi", "Vui lòng chọn đợt và phòng ban")
                return
            batch_id = batch_map.get(batch_combo.get())
            dept_id = dept_map.get(dept_combo.get())
            self.db.add_department_award(dept_id, batch_id, note_dept.get().strip())
            show_info("Thành công", "Đã phân khen thưởng cho phòng ban")
            self.load_recent_assignments()

        ctk.CTkButton(frm, text="➕ Phân cho phòng ban", command=add_dept_award, fg_color="#06b6d4").pack(fill="x", pady=6)

    # -------------------------
    # Simple CRUD dialogs for Years / Titles / Authorities
    # -------------------------
    def open_years_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Quản lý Năm khen thưởng")
        center_window(dlg, 420, 320)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg); frm.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(frm, text="Năm:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        year_ent = ctk.CTkEntry(frm); year_ent.pack(fill="x", pady=6)
        def add():
            y = year_ent.get().strip()
            if not y.isdigit() or len(y) != 4:
                show_error("Lỗi", "Nhập năm hợp lệ (YYYY)")
                return
            if self.db.add_award_year(int(y)):
                show_info("Thành công", "Đã thêm năm")
                year_ent.delete(0, "end")
            else:
                show_error("Lỗi", "Năm đã tồn tại")
        ctk.CTkButton(frm, text="➕ Thêm năm", command=add, fg_color="#10b981").pack(fill="x", pady=6)

        # list years
        tree = ttk.Treeview(frm, columns=("ID","Year"), show="headings", height=8)
        tree.heading("ID", text="ID"); tree.heading("Year", text="Year")
        tree.column("ID", width=60, anchor="center"); tree.column("Year", width=120, anchor="center")
        tree.pack(fill="both", expand=True, pady=(8,0))
        def load():
            for i in tree.get_children(): tree.delete(i)
            for r in self.db.get_all_award_years():
                tree.insert("", "end", values=r)
        load()

    def open_titles_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Quản lý Danh hiệu")
        center_window(dlg, 640, 480)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg); frm.pack(fill="both", expand=True, padx=12, pady=12)
        # form
        ctk.CTkLabel(frm, text="Tên danh hiệu:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        name_ent = ctk.CTkEntry(frm); name_ent.pack(fill="x", pady=6)
        ctk.CTkLabel(frm, text="Scope (ca_nhan | tap_the):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        scope_combo = ctk.CTkComboBox(frm, values=["ca_nhan","tap_the"], state="readonly"); scope_combo.set("ca_nhan"); scope_combo.pack(fill="x", pady=6)
        ctk.CTkLabel(frm, text="Level (co_so | tinh | trung_uong):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        # level_combo = ctk.CTkComboBox(frm, values=["co_so","tinh","trung_uong"], state="readonly"); level_combo.set("co_so"); level_combo.pack(fill="x", pady=6)
        level_combo = ctk.CTkEntry(frm); level_combo.insert(0, "co_so"); level_combo.pack(fill="x", pady=6)
        def add():
            name = name_ent.get().strip()
            scope = scope_combo.get()
            level = level_combo.get()
            if not name:
                show_error("Lỗi", "Nhập tên danh hiệu")
                return
            self.db.add_award_title(name, scope, level)
            show_info("Thành công", "Đã thêm danh hiệu")
            name_ent.delete(0, "end")
            load()
        ctk.CTkButton(frm, text="➕ Thêm danh hiệu", command=add, fg_color="#10b981").pack(fill="x", pady=6)

        tree = ttk.Treeview(frm, columns=("ID","Name","Scope","Level"), show="headings", height=12)
        for c in ("ID","Name","Scope","Level"):
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, pady=(8,0))
        def load():
            for i in tree.get_children(): tree.delete(i)
            for r in self.db.get_all_award_titles():
                tree.insert("", "end", values=r)
        load()

    def open_authorities_dialog(self):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Quản lý Cơ quan ban hành")
        center_window(dlg, 480, 360)
        dlg.transient(self.app)
        dlg.grab_set()

        frm = ctk.CTkFrame(dlg); frm.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(frm, text="Tên cơ quan:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        name_ent = ctk.CTkEntry(frm); name_ent.pack(fill="x", pady=6)
        def add():
            name = name_ent.get().strip()
            if not name:
                show_error("Lỗi", "Nhập tên cơ quan")
                return
            self.db.add_award_authority(name)
            show_info("Thành công", "Đã thêm cơ quan")
            name_ent.delete(0, "end")
            load()
        ctk.CTkButton(frm, text="➕ Thêm cơ quan", command=add, fg_color="#10b981").pack(fill="x", pady=6)

        tree = ttk.Treeview(frm, columns=("ID","Name"), show="headings", height=10)
        tree.heading("ID", text="ID"); tree.heading("Name", text="Name")
        tree.pack(fill="both", expand=True, pady=(8,0))
        def load():
            for i in tree.get_children(): tree.delete(i)
            for r in self.db.get_all_award_authorities():
                tree.insert("", "end", values=r)
        load()

    # -------------------------
    # Delete assignment callbacks
    # -------------------------
    def delete_selected_staff_award(self):
        sel = self.tree_staff_awards.selection()
        if not sel:
            return
        sa_id = self.tree_staff_awards.item(sel[0])['values'][0]
        if ask_confirm("Xác nhận", "Bạn có muốn xóa khen thưởng này cho nhân viên?"):
            try:
                self.db.delete_staff_award(sa_id)
                show_info("Thành công", "Đã xóa")
                self.load_recent_assignments()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa: {e}")

    def delete_selected_dept_award(self):
        sel = self.tree_dept_awards.selection()
        if not sel:
            return
        da_id = self.tree_dept_awards.item(sel[0])['values'][0]
        if ask_confirm("Xác nhận", "Bạn có muốn xóa khen thưởng này cho phòng ban?"):
            try:
                self.db.delete_department_award(da_id)
                show_info("Thành công", "Đã xóa")
                self.load_recent_assignments()
            except Exception as e:
                show_error("Lỗi", f"Không thể xóa: {e}")


# 
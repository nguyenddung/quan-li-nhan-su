"""
awards.py
Quản lý danh hiệu và năm khen thưởng:
- Hiển thị danh sách năm và danh hiệu
- Thêm năm, thêm danh hiệu
"""
import customtkinter as ctk
from ..dialogs import center_window, show_info, show_error

class AwardsView:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def render(self):
        grid = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        # LEFT: Year
        year_frame = ctk.CTkFrame(grid, fg_color="white", corner_radius=12)
        year_frame.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=4)
        ctk.CTkLabel(year_frame, text="📅 NĂM KHEN THƯỞNG", font=ctk.CTkFont(size=14, weight="bold"), text_color="white", fg_color="#4f46e5").pack(fill="x")

        year_scroll = ctk.CTkScrollableFrame(year_frame)
        year_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        if self.app.is_admin:
            ctk.CTkButton(year_scroll, text="➕ Thêm năm mới", fg_color="#10b981", command=self.add_year_dialog).pack(fill="x", pady=8)

        years = self.db.get_all_award_years()
        for y in years:
            card = ctk.CTkFrame(year_scroll, fg_color="#f1f5f9", corner_radius=8)
            card.pack(fill="x", pady=6)
            ctk.CTkLabel(card, text=f"🗓️ Năm {y[1]}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1e293b").pack(padx=8, pady=8)

        # RIGHT: Titles
        title_frame = ctk.CTkFrame(grid, fg_color="white", corner_radius=12)
        title_frame.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=4)
        ctk.CTkLabel(title_frame, text="🏅 DANH HIỆU", font=ctk.CTkFont(size=14, weight="bold"), text_color="white", fg_color="#eab308").pack(fill="x")

        title_scroll = ctk.CTkScrollableFrame(title_frame)
        title_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        if self.app.is_admin:
            ctk.CTkButton(title_scroll, text="➕ Thêm danh hiệu", fg_color="#10b981", command=self.add_title_dialog).pack(fill="x", pady=8)

        titles = self.db.get_all_award_titles()
        for t in titles:
            card = ctk.CTkFrame(title_scroll, fg_color="#fef3c7", corner_radius=8, border_width=1, border_color="#fbbf24")
            card.pack(fill="x", pady=6)
            ctk.CTkLabel(card, text=f"🏆 {t[1]}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#78350f").pack(anchor="w", padx=8, pady=(8,0))
            ctk.CTkLabel(card, text=f"Phạm vi: {t[2] if t[2] else 'Chưa xác định'}", font=ctk.CTkFont(size=11), text_color="#92400e").pack(anchor="w", padx=8, pady=(0,8))

    def add_year_dialog(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Thêm năm khen thưởng")
        center_window(dialog, 380, 180)
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Năm khen thưởng (YYYY):", font=ctk.CTkFont(size=12, weight="bold")).pack(padx=12, pady=(20,6))
        year_ent = ctk.CTkEntry(dialog, height=36); year_ent.pack(fill="x", padx=12)

        def save():
            y = year_ent.get().strip()
            if not y.isdigit() or len(y) != 4:
                show_error("Lỗi", "Nhập năm hợp lệ (4 chữ số)")
                return
            ok = self.db.add_award_year(int(y))
            if ok:
                show_info("Thành công", f"Đã thêm năm {y}")
                dialog.destroy()
                self.render()
            else:
                show_error("Lỗi", "Năm đã tồn tại")

        ctk.CTkButton(dialog, text="💾 Lưu", command=save, fg_color="#10b981").pack(fill="x", padx=12, pady=12)

    def add_title_dialog(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Thêm danh hiệu")
        center_window(dialog, 480, 260)
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Tên danh hiệu:", font=ctk.CTkFont(size=12, weight="bold")).pack(padx=12, pady=(14,6), anchor="w")
        name_ent = ctk.CTkEntry(dialog, height=36); name_ent.pack(fill="x", padx=12)

        ctk.CTkLabel(dialog, text="Phạm vi:", font=ctk.CTkFont(size=12, weight="bold")).pack(padx=12, pady=(12,6), anchor="w")
        scope_combo = ctk.CTkComboBox(dialog, values=["Cấp cơ sở","Cấp Bộ","Cấp Nhà nước","Cấp Tỉnh/Thành phố"], state="readonly")
        scope_combo.set("Cấp cơ sở"); scope_combo.pack(fill="x", padx=12)

        def save():
            name = name_ent.get().strip()
            scope = scope_combo.get()
            if not name:
                show_error("Lỗi", "Vui lòng nhập tên danh hiệu")
                return
            self.db.add_award_title(name, scope)
            show_info("Thành công", "Đã thêm danh hiệu")
            dialog.destroy()
            self.render()

        ctk.CTkButton(dialog, text="💾 Lưu danh hiệu", command=save, fg_color="#10b981").pack(fill="x", padx=12, pady=12)
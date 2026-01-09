"""
gui.py
HRMApp: lớp chính chịu trách nhiệm tạo layout (sidebar + header + content)
và chuyển đổi giữa các view module trong hrm_app.views.
"""
import customtkinter as ctk
import tkinter as tk

from .db import DatabaseManager
from .views import dashboard, departments, staff, awards, documents

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class HRMApp(ctk.CTk):
    """
    HRMApp là cửa sổ chính, giữ một instance DatabaseManager (self.db)
    và is_admin flag để bật/tắt quyền chỉnh sửa.
    """
    def __init__(self, is_admin=True, db_name="hrm_ultimate.db"):
        super().__init__()
        self.is_admin = is_admin
        self.title("QANGNINH ULTIMATE - Database Management System")
        self.geometry("1200x800")
        self.state("zoomed")

        # Database
        self.db = DatabaseManager(db_name=db_name)

        # Layout cơ bản
        self.create_layout()

        # Mặc định hiển thị dashboard
        self.show_dashboard()

    def create_layout(self):
        # cấu hình grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#312e81")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="#1e1b4b", corner_radius=0)
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(logo_frame, text="QUANGNINH ULTIMATE", font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=12)
        ctk.CTkLabel(logo_frame, text="DATABASE MANAGEMENT SYSTEM", font=ctk.CTkFont(size=9), text_color="#94a3b8").pack()

        # Buttons menu
        self.create_menu_button("📊 Tổng quan", 1, self.show_dashboard, active=True)
        self.create_menu_button("🏢 Phòng ban", 2, self.show_departments)
        self.create_menu_button("👥 Nhân sự", 3, self.show_staff)
        self.create_menu_button("🏆 Danh hiệu & Năm", 4, self.show_awards)
        # self.create_menu_button("📄 Hồ sơ tài liệu", 5, self.show_documents)

        # MAIN CONTENT
        self.main_content = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self.main_content, height=70, fg_color="white", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.page_title = ctk.CTkLabel(self.header, text="📊 TỔNG QUAN", font=ctk.CTkFont(size=18, weight="bold"), text_color="#1e293b")
        self.page_title.pack(side="left", padx=20, pady=18)

        # Content scrollable
        self.content_frame = ctk.CTkScrollableFrame(self.main_content, fg_color="#f8fafc")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

    def create_menu_button(self, text, row, command, active=False):
        btn = ctk.CTkButton(self.sidebar, text=text, font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#4338ca" if active else "transparent", hover_color="#4338ca",
                            corner_radius=10, height=40, anchor="w", command=command)
        btn.grid(row=row, column=0, padx=16, pady=8, sticky="ew")
        return btn

    def clear_content(self):
        """Xóa widget hiện có trong content_frame trước khi render view mới"""
        for w in self.content_frame.winfo_children():
            w.destroy()

    # Các phương thức show_xxx sẽ gọi module tương ứng để render view
    def show_dashboard(self):
        self.clear_content()
        self.page_title.configure(text="📊 TỔNG QUAN")
        dashboard.DashboardView(self, self.db).render()

    def show_departments(self):
        self.clear_content()
        self.page_title.configure(text="🏢 QUẢN LÝ PHÒNG BAN")
        departments.DepartmentsView(self, self.db).render()

    def show_staff(self):
        self.clear_content()
        self.page_title.configure(text="👥 QUẢN LÝ NHÂN SỰ")
        staff.StaffView(self, self.db).render()

    def show_awards(self):
        self.clear_content()
        self.page_title.configure(text="🏆 DANH HIỆU & NĂM KHEN THƯỞNG")
        awards.AwardsView(self, self.db).render()

    def show_documents(self):
        self.clear_content()
        self.page_title.configure(text="📄 QUẢN LÝ HỒ SƠ TÀI LIỆU")
        documents.DocumentsView(self, self.db).render()
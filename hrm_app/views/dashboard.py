"""
dashboard.py
View tổng quan: hiển thị 4 card thống kê và biểu đồ đơn giản.
"""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardView:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def create_stat_card(self, parent, title, value, color, column):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        card.grid(row=0, column=column, padx=8, pady=8, sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748b").pack(pady=(12,6))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=color).pack(pady=(0,12))

    def render(self):
        # Lấy thống kê
        dept_count, staff_count, award_count, doc_count = self.db.get_statistics()

        stats_frame = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 16))
        self.create_stat_card(stats_frame, "🏢 Phòng ban", str(dept_count), "#3b82f6", 0)
        self.create_stat_card(stats_frame, "👥 Nhân sự", str(staff_count), "#8b5cf6", 1)
        self.create_stat_card(stats_frame, "🏆 Khen thưởng", str(award_count), "#eab308", 2)
        self.create_stat_card(stats_frame, "📄 Văn bản", str(doc_count), "#10b981", 3)

        # Biểu đồ mẫu (dùng matplotlib)
        chart_frame = ctk.CTkFrame(self.app.content_frame, fg_color="white", corner_radius=12)
        chart_frame.pack(fill="both", expand=True, pady=6)

        ctk.CTkLabel(chart_frame, text="THỐNG KÊ KHEN THƯỞNG THEO THÁNG", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=12)

        fig = Figure(figsize=(10,4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        months = ['T1','T2','T3','T4','T5','T6']
        values = [5,12,8,25,18,32]
        ax.plot(months, values, marker='o', linewidth=2, color='#4f46e5')
        ax.fill_between(months, values, alpha=0.15, color='#4f46e5')
        ax.set_xlabel("Tháng")
        ax.set_ylabel("Số lượng")
        ax.grid(True, linestyle='--', alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=8)
"""
dashboard.py
View tổng quan: hiển thị 4 card thống kê và biểu đồ khen thưởng theo năm.
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

    def get_awards_by_year(self):
        """
        Lấy thống kê số lượng khen thưởng (cả cá nhân và tập thể) theo năm
        Returns: dict {year: count}
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        # Thống kê khen thưởng cá nhân theo năm
        cur.execute('''
            SELECT ay.year, COUNT(sa.id) as count
            FROM award_years ay
            LEFT JOIN award_batches ab ON ab.award_year_id = ay.id
            LEFT JOIN staff_awards sa ON sa.award_batch_id = ab.id
            GROUP BY ay.year
            ORDER BY ay.year
        ''')
        staff_awards = {row[0]: row[1] for row in cur.fetchall()}
        
        # Thống kê khen thưởng tập thể theo năm
        cur.execute('''
            SELECT ay.year, COUNT(da.id) as count
            FROM award_years ay
            LEFT JOIN award_batches ab ON ab.award_year_id = ay.id
            LEFT JOIN department_awards da ON da.award_batch_id = ab.id
            GROUP BY ay.year
            ORDER BY ay.year
        ''')
        dept_awards = {row[0]: row[1] for row in cur.fetchall()}
        
        conn.close()
        
        # Gộp cả hai loại khen thưởng
        all_years = set(staff_awards.keys()) | set(dept_awards.keys())
        total_awards = {}
        for year in all_years:
            total_awards[year] = staff_awards.get(year, 0) + dept_awards.get(year, 0)
        
        return total_awards, staff_awards, dept_awards

    def get_awards_by_level(self):
        """
        Lấy thống kê khen thưởng theo cấp (co_so, tinh, trung_uong)
        Returns: dict {level: count}
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT at.level, COUNT(sa.id) + COUNT(da.id) as total
            FROM award_titles at
            LEFT JOIN award_batches ab ON ab.award_title_id = at.id
            LEFT JOIN staff_awards sa ON sa.award_batch_id = ab.id
            LEFT JOIN department_awards da ON da.award_batch_id = ab.id
            GROUP BY at.level
            ORDER BY total DESC
        ''')
        
        levels = {}
        for row in cur.fetchall():
            if row[0]:  # Kiểm tra level không null
                levels[row[0]] = row[1]
        
        conn.close()
        return levels

    def render(self):
        # Lấy thống kê tổng quan
        dept_count, staff_count, award_count, doc_count = self.db.get_statistics()

        # Card thống kê tổng quan
        stats_frame = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 16))
        self.create_stat_card(stats_frame, "🏢 Phòng ban", str(dept_count), "#3b82f6", 0)
        self.create_stat_card(stats_frame, "👥 Nhân sự", str(staff_count), "#8b5cf6", 1)
        self.create_stat_card(stats_frame, "🏆 Khen thưởng", str(award_count), "#eab308", 2)
        self.create_stat_card(stats_frame, "📄 Văn bản", str(doc_count), "#10b981", 3)

        # Container cho các biểu đồ
        charts_container = ctk.CTkFrame(self.app.content_frame, fg_color="transparent")
        charts_container.pack(fill="both", expand=True, pady=6)

        # Biểu đồ 1: Thống kê khen thưởng theo năm
        chart_frame_1 = ctk.CTkFrame(charts_container, fg_color="white", corner_radius=12)
        chart_frame_1.pack(fill="both", expand=True, pady=(0, 8))

        ctk.CTkLabel(chart_frame_1, text="📊 THỐNG KÊ KHEN THƯỞNG THEO NĂM", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=12)

        # Lấy dữ liệu
        total_awards, staff_awards, dept_awards = self.get_awards_by_year()
        
        if total_awards:
            years = sorted(total_awards.keys())
            staff_values = [staff_awards.get(y, 0) for y in years]
            dept_values = [dept_awards.get(y, 0) for y in years]
            
            # Vẽ biểu đồ cột chồng
            fig1 = Figure(figsize=(10, 4), dpi=100, facecolor='white')
            ax1 = fig1.add_subplot(111)
            
            x_pos = range(len(years))
            width = 0.6
            
            # Vẽ cột chồng
            ax1.bar(x_pos, staff_values, width, label='Cá nhân', color='#3b82f6', alpha=0.8)
            ax1.bar(x_pos, dept_values, width, bottom=staff_values, label='Tập thể', color='#10b981', alpha=0.8)
            
            ax1.set_xlabel('Năm', fontsize=11, fontweight='bold')
            ax1.set_ylabel('Số lượng', fontsize=11, fontweight='bold')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(years, rotation=0)
            ax1.legend(loc='upper right', fontsize=10)
            ax1.grid(axis='y', alpha=0.3, linestyle='--')
            ax1.set_axisbelow(True)
            
            # Thêm giá trị lên cột
            for i, year in enumerate(years):
                total = staff_values[i] + dept_values[i]
                if total > 0:
                    ax1.text(i, total, str(total), ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            fig1.tight_layout()
            
            canvas1 = FigureCanvasTkAgg(fig1, chart_frame_1)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 12))
        else:
            ctk.CTkLabel(chart_frame_1, text="Chưa có dữ liệu khen thưởng", 
                        text_color="#94a3b8").pack(pady=40)

        # Biểu đồ 2: Thống kê theo cấp khen thưởng
        chart_frame_2 = ctk.CTkFrame(charts_container, fg_color="white", corner_radius=12)
        chart_frame_2.pack(fill="both", expand=True)

        ctk.CTkLabel(chart_frame_2, text="🏅 THỐNG KÊ THEO CẤP KHEN THƯỞNG", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=12)

        levels_data = self.get_awards_by_level()
        
        if levels_data:
            # Mapping tên cấp
            level_names = {
                'co_so': 'Cơ sở',
                'tinh': 'Tỉnh',
                'trung_uong': 'Trung ương'
            }
            
            labels = [level_names.get(k, k) for k in levels_data.keys()]
            values = list(levels_data.values())
            colors = ['#3b82f6', '#8b5cf6', '#eab308', '#10b981', '#ef4444'][:len(labels)]
            
            fig2 = Figure(figsize=(10, 3.5), dpi=100, facecolor='white')
            ax2 = fig2.add_subplot(111)
            
            # Vẽ biểu đồ tròn
            wedges, texts, autotexts = ax2.pie(values, labels=labels, autopct='%1.1f%%',
                                                colors=colors, startangle=90,
                                                textprops={'fontsize': 10, 'weight': 'bold'})
            
            # Tô màu chữ phần trăm
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
            
            # Thêm legend với số lượng
            legend_labels = [f'{labels[i]}: {values[i]}' for i in range(len(labels))]
            ax2.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=10)
            
            fig2.tight_layout()
            
            canvas2 = FigureCanvasTkAgg(fig2, chart_frame_2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 12))
        else:
            ctk.CTkLabel(chart_frame_2, text="Chưa có dữ liệu phân loại cấp", 
                        text_color="#94a3b8").pack(pady=40)
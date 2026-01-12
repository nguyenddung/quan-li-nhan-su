# hrm_app/db.py
# Database layer (cập nhật): tự động gán STT cho nhân viên theo phòng ban,
# và resequence STT khi xóa nhân viên.

import sqlite3
import random
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_name="hrm_ultimate.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_database(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # departments
        cur.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')

        # staffs
        cur.execute('''
            CREATE TABLE IF NOT EXISTS staffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stt INTEGER,
                full_name TEXT NOT NULL,
                dob DATE,
                position TEXT,
                phone TEXT,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE CASCADE
            )
        ''')

        # documents
        cur.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                loai_ho_so TEXT,
                so_va_ky_hieu TEXT,
                ngay_thang TEXT,
                ten_loai_trich_yeu_noi_dung TEXT,
                so_to INTEGER,
                ghi_chu TEXT,
                file_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staffs (id) ON DELETE CASCADE
            )
        ''')

        # work_histories
        cur.execute('''
            CREATE TABLE IF NOT EXISTS work_histories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                decision_no TEXT,
                ngay_quyet_dinh DATE,
                cac_vi_tri_cong_tac TEXT,
                giu_chuc_vu DATE,
                cong_tac_tai_cq DATE,
                ghi_chu TEXT,
                FOREIGN KEY (staff_id) REFERENCES staffs(id) ON DELETE CASCADE
            )
        ''')

        # award_years (giữ nguyên)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER UNIQUE NOT NULL
            )
        ''')

        # award_titles: thêm column level nếu cần; scope có thể đã tồn tại ở schema cũ
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                scope TEXT,
                level TEXT
            )
        ''')

        # award_authorities (mới)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_authorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        # award_batches: ensure authority_id column exists
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                award_year_id INTEGER NOT NULL,
                award_title_id INTEGER NOT NULL,
                authority_id INTEGER,
                decision_no TEXT,
                decision_date DATE,
                note TEXT,
                FOREIGN KEY (award_year_id) REFERENCES award_years(id) ON DELETE CASCADE,
                FOREIGN KEY (award_title_id) REFERENCES award_titles(id) ON DELETE CASCADE,
                FOREIGN KEY (authority_id) REFERENCES award_authorities(id) ON DELETE SET NULL
            )
        ''')
      
        # staff_awards (giữ nguyên schema nhưng đảm bảo FK)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS staff_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                award_batch_id INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY (staff_id) REFERENCES staffs (id) ON DELETE CASCADE,
                FOREIGN KEY (award_batch_id) REFERENCES award_batches (id) ON DELETE CASCADE
            )
        ''')

        # department_awards
        cur.execute('''
            CREATE TABLE IF NOT EXISTS department_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL,
                award_batch_id INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE CASCADE,
                FOREIGN KEY (award_batch_id) REFERENCES award_batches (id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

        # (Tùy chọn) Add some sample data if empty
        self._ensure_complete_sample_data()

   
    # ----------------------------
    # Award Years
    # ----------------------------
    def get_all_award_years(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, year FROM award_years ORDER BY year DESC")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_year(self, year):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO award_years (year) VALUES (?)", (year,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def delete_award_year(self, year_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM award_years WHERE id = ?", (year_id,))
        conn.commit()
        conn.close()

    # ----------------------------
    # Award Titles
    # ----------------------------
    def get_all_award_titles(self):
        """Trả về id, name, scope, level"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, scope, level FROM award_titles ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_title(self, name, scope, level):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO award_titles (name, scope, level) VALUES (?, ?, ?)", (name, scope, level))
        conn.commit()
        conn.close()

    def update_award_title(self, title_id, name, scope, level):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE award_titles SET name = ?, scope = ?, level = ? WHERE id = ?", (name, scope, level, title_id))
        conn.commit()
        conn.close()

    def delete_award_title(self, title_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM award_titles WHERE id = ?", (title_id,))
        conn.commit()
        conn.close()

    # ----------------------------
    # Award Authorities
    # ----------------------------
    def get_all_award_authorities(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM award_authorities ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_authority(self, name):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO award_authorities (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()

    def delete_award_authority(self, auth_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM award_authorities WHERE id = ?", (auth_id,))
        conn.commit()
        conn.close()

    # ----------------------------
    # Award Batches (Đợt / Quyết định)
    # ----------------------------
    def get_all_award_batches(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT ab.id, ay.year, at.name, at.level, aa.name, ab.decision_no, ab.decision_date, ab.note, ab.award_year_id, ab.award_title_id, ab.authority_id
            FROM award_batches ab
            LEFT JOIN award_years ay ON ab.award_year_id = ay.id
            LEFT JOIN award_titles at ON ab.award_title_id = at.id
            LEFT JOIN award_authorities aa ON ab.authority_id = aa.id
            ORDER BY ab.decision_date DESC
        ''')
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_batch(self, award_year_id, award_title_id, authority_id, decision_no, decision_date, note):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO award_batches (award_year_id, award_title_id, authority_id, decision_no, decision_date, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (award_year_id, award_title_id, authority_id, decision_no, decision_date, note))
        conn.commit()
        conn.close()

    def update_award_batch(self, batch_id, award_year_id, award_title_id, authority_id, decision_no, decision_date, note):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE award_batches
            SET award_year_id = ?, award_title_id = ?, authority_id = ?, decision_no = ?, decision_date = ?, note = ?
            WHERE id = ?
        ''', (award_year_id, award_title_id, authority_id, decision_no, decision_date, note, batch_id))
        conn.commit()
        conn.close()

    def delete_award_batch(self, batch_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM award_batches WHERE id = ?", (batch_id,))
        conn.commit()
        conn.close()

    # ----------------------------
    # Staff awards (khen cho cá nhân)
    # ----------------------------
    def add_staff_award(self, staff_id, award_batch_id, note):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO staff_awards (staff_id, award_batch_id, note) VALUES (?, ?, ?)", (staff_id, award_batch_id, note))
        conn.commit()
        conn.close()

    def delete_staff_award(self, sa_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM staff_awards WHERE id = ?", (sa_id,))
        conn.commit()
        conn.close()

    def get_staff_awards_by_staff(self, staff_id):
        """
        Trả về danh sách khen thưởng cho 1 nhân viên (dùng query mẫu của bạn).
        Kết quả: list tuple gồm (full_name, year, danh_hieu, level, decision_no, decision_date, authority_name, staff_award_id, award_batch_id, note)
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT
                s.full_name,
                ay.year,
                at.name AS danh_hieu,
                at.level AS cap,
                ab.decision_no,
                ab.decision_date,
                aa.name AS co_quan,
                sa.id AS staff_award_id,
                sa.award_batch_id,
                sa.note
            FROM staffs s
            JOIN staff_awards sa ON s.id = sa.staff_id
            JOIN award_batches ab ON sa.award_batch_id = ab.id
            JOIN award_titles at ON ab.award_title_id = at.id
            JOIN award_years ay ON ab.award_year_id = ay.id
            LEFT JOIN award_authorities aa ON ab.authority_id = aa.id
            WHERE s.id = ?
            ORDER BY ay.year DESC, ab.decision_date DESC
        ''', (staff_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ----------------------------
    # Department awards (khen cho tập thể)
    # ----------------------------
    def add_department_award(self, department_id, award_batch_id, note):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO department_awards (department_id, award_batch_id, note) VALUES (?, ?, ?)", (department_id, award_batch_id, note))
        conn.commit()
        conn.close()

    def delete_department_award(self, da_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM department_awards WHERE id = ?", (da_id,))
        conn.commit()
        conn.close()

    def get_department_awards_by_department(self, department_id):
        """
        Trả về danh sách khen thưởng cho 1 phòng ban.
        Kết quả: (department_name, year, title_name, decision_no, decision_date, authority_name, department_award_id, award_batch_id, note)
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT
                d.name,
                ay.year,
                at.name,
                ab.decision_no,
                ab.decision_date,
                aa.name AS co_quan,
                da.id AS department_award_id,
                da.award_batch_id,
                da.note
            FROM departments d
            JOIN department_awards da ON d.id = da.department_id
            JOIN award_batches ab ON da.award_batch_id = ab.id
            JOIN award_titles at ON ab.award_title_id = at.id
            JOIN award_years ay ON ab.award_year_id = ay.id
            LEFT JOIN award_authorities aa ON ab.authority_id = aa.id
            WHERE d.id = ?
            ORDER BY ay.year DESC, ab.decision_date DESC
        ''', (department_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    # ----------------------------
    # Helpful report queries
    # ----------------------------
    def get_awards_summary_by_year(self, year):
        """Trả về tóm tắt (số cá nhân/tập thể) cho 1 năm"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT ay.year,
                SUM(CASE WHEN at.scope = 'ca_nhan' THEN 1 ELSE 0 END) as ca_nhan_count,
                SUM(CASE WHEN at.scope = 'tap_the' THEN 1 ELSE 0 END) as tap_the_count
            FROM award_batches ab
            JOIN award_years ay ON ab.award_year_id = ay.id
            JOIN award_titles at ON ab.award_title_id = at.id
            LEFT JOIN staff_awards sa ON sa.award_batch_id = ab.id
            LEFT JOIN department_awards da ON da.award_batch_id = ab.id
            WHERE ay.year = ?
            GROUP BY ay.year
        ''', (year,))
        rows = cur.fetchall()
        conn.close()
        return rows
    def add_sample_data(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM departments")
        if cur.fetchone()[0] == 0:
            sample_depts = [
                ("Phòng Công nghệ thông tin", "Quản lý hệ thống và phát triển phần mềm"),
                ("Phòng Nhân sự", "Quản lý nhân sự và tuyển dụng"),
                ("Phòng Kế toán", "Quản lý tài chính và kế toán"),
            ]
            cur.executemany("INSERT INTO departments (name, description) VALUES (?, ?)", sample_depts)

            # Thêm nhân viên mẫu (stt được tự gán bằng add_staff)
            # để gọi add_staff với stt=None (hàm tự xử lý)
            conn = self.get_connection()
            conn.close()

            # Thêm bản ghi award mẫu
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO award_years (year) VALUES (2023)")
            cur.execute("INSERT INTO award_years (year) VALUES (2024)")
            cur.execute("INSERT INTO award_titles (name, scope) VALUES ('Chiến sĩ thi đua cơ sở', 'Cấp cơ sở')")
            cur.execute("INSERT INTO award_titles (name, scope) VALUES ('Lao động tiên tiến', 'Cấp cơ sở')")
            conn.commit()
            conn.close()
        conn.close()

    # -----------------------
    # Helpers for STT
    # -----------------------
    def _get_next_stt_for_department(self, department_id):
        """Trả về số STT tiếp theo cho department_id: max(stt)+1 (0 -> 1)"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(stt), 0) FROM staffs WHERE department_id = ?", (department_id,))
        next_stt = cur.fetchone()[0] + 1
        conn.close()
        return next_stt

    def _resequence_stt_for_department(self, department_id):
        """
        Sắp lại STT cho tất cả nhân viên trong department theo thứ tự id (hoặc theo created order),
        gán lại stt = 1..n. Gọi sau khi xóa để giữ liên tục STT trong phòng ban.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM staffs WHERE department_id = ? ORDER BY id", (department_id,))
        rows = cur.fetchall()
        for idx, (staff_id,) in enumerate(rows, start=1):
            cur.execute("UPDATE staffs SET stt = ? WHERE id = ?", (idx, staff_id))
        conn.commit()
        conn.close()

    # -----------------------
    # Departments CRUD
    # -----------------------
    def get_all_departments(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM departments ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_department(self, name, description):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO departments (name, description) VALUES (?, ?)", (name, description))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def update_department(self, dept_id, name, description):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE departments SET name=?, description=? WHERE id=?", (name, description, dept_id))
        conn.commit()
        conn.close()

    def delete_department(self, dept_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM departments WHERE id=?", (dept_id,))
        conn.commit()
        conn.close()

    # -----------------------
    # Staffs CRUD + helper
    # -----------------------
    def get_all_staffs(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT s.id, s.stt, s.full_name, s.position, s.phone, s.dob, d.name
            FROM staffs s
            LEFT JOIN departments d ON s.department_id = d.id
            ORDER BY s.id
        ''')
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_staffs_by_department(self, department_id):
        """Trả về list nhân viên thuộc department_id (có stt)"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT s.id, s.stt, s.full_name, s.position, s.phone, s.dob, d.name
            FROM staffs s
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE s.department_id = ?
            ORDER BY s.stt ASC
        ''', (department_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def search_staffs_by_name(self, query):
        """Tìm nhân sự theo tên (LIKE)"""
        conn = self.get_connection()
        cur = conn.cursor()
        likeq = f"%{query}%"
        cur.execute('''
            SELECT s.id, s.stt, s.full_name, s.position, s.phone, s.dob, d.name
            FROM staffs s
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE s.full_name LIKE ?
            ORDER BY s.id
        ''', (likeq,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_staff(self, stt, full_name, dob, position, phone, department_id):
        """
        Thêm nhân viên. Nếu stt là None, tự gán stt = next trong phòng ban.
        (Gọi với stt=None khi người dùng không nhập STT)
        """
        conn = self.get_connection()
        cur = conn.cursor()
        if stt is None:
            stt_to_use = self._get_next_stt_for_department(department_id)
        else:
            stt_to_use = stt
        cur.execute('''
            INSERT INTO staffs (stt, full_name, dob, position, phone, department_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (stt_to_use, full_name, dob, position, phone, department_id))
        conn.commit()
        conn.close()

    def update_staff(self, staff_id, stt, full_name, dob, position, phone, department_id):
        """
        Cập nhật nhân viên.
        - Nếu stt là None: không thay đổi stt hiện tại.
        - Nếu thay đổi department, ta set stt mới tự động (append) và resequence phòng cũ.
        """
        conn = self.get_connection()
        cur = conn.cursor()

        # Lấy department cũ của staff
        cur.execute("SELECT department_id FROM staffs WHERE id = ?", (staff_id,))
        row = cur.fetchone()
        old_dept = row[0] if row else None

        # Nếu department_id thay đổi và stt không được cung cấp -> gán stt mới cho phòng mới
        if old_dept is not None and old_dept != department_id:
            # cập nhật rồi resequence phòng cũ
            # set stt mới cho staff khi chuyển phòng
            new_stt = self._get_next_stt_for_department(department_id) if stt is None else stt
            cur.execute('''
                UPDATE staffs SET stt=?, full_name=?, dob=?, position=?, phone=?, department_id=?
                WHERE id=?
            ''', (new_stt, full_name, dob, position, phone, department_id, staff_id))
            conn.commit()
            # resequence phòng cũ
            self._resequence_stt_for_department(old_dept)
            conn.close()
            return

        # Nếu stt provided not None -> set it, else preserve current stt
        if stt is None:
            # preserve current stt
            cur.execute('''
                UPDATE staffs SET full_name=?, dob=?, position=?, phone=?, department_id=?
                WHERE id=?
            ''', (full_name, dob, position, phone, department_id, staff_id))
        else:
            cur.execute('''
                UPDATE staffs SET stt=?, full_name=?, dob=?, position=?, phone=?, department_id=?
                WHERE id=?
            ''', (stt, full_name, dob, position, phone, department_id, staff_id))
        conn.commit()
        conn.close()

    def delete_staff(self, staff_id):
        """
        Xóa staff, sau đó resequence stt cho phòng ban tương ứng để đảm bảo stt là 1..n
        """
        # Lấy department trước khi xóa
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT department_id FROM staffs WHERE id = ?", (staff_id,))
        row = cur.fetchone()
        dept_id = row[0] if row else None

        cur.execute("DELETE FROM staffs WHERE id=?", (staff_id,))
        conn.commit()
        conn.close()

        if dept_id is not None:
            # resequence
            self._resequence_stt_for_department(dept_id)

    # -----------------------
    # Award methods (unchanged)
    # -----------------------
    def get_all_award_years(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM award_years ORDER BY year DESC")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_year(self, year):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO award_years (year) VALUES (?)", (year,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_all_award_titles(self):
        """Trả về id, name, scope, level"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, scope, level FROM award_titles ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_title(self, name, scope, level):
        """
        Thêm 1 danh hiệu khen thưởng.
        - name: tên danh hiệu
        - scope: 'ca_nhan' hoặc 'tap_the'
        - level: 'co_so' | 'tinh' | 'trung_uong'
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO award_titles (name, scope, level) VALUES (?, ?, ?)", (name, scope, level))
        conn.commit()
        conn.close()
        # -----------------------
    # Documents methods (unchanged)
    # -----------------------
    def get_all_documents(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT d.id, s.full_name, d.loai_ho_so, d.so_va_ky_hieu, d.ngay_thang, d.file_url
            FROM documents d
            LEFT JOIN staffs s ON d.staff_id = s.id
            ORDER BY d.id
        ''')
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_documents_by_staff(self, staff_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai_trich_yeu_noi_dung, so_to, ghi_chu, file_url, created_at
            FROM documents
            WHERE staff_id = ?
            ORDER BY created_at DESC
        ''', (staff_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_document(self, staff_id, loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai, so_to, ghi_chu, file_url):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO documents (staff_id, loai_ho_so, so_va_ky_hieu, ngay_thang,
                                   ten_loai_trich_yeu_noi_dung, so_to, ghi_chu, file_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (staff_id, loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai, so_to, ghi_chu, file_url))
        conn.commit()
        conn.close()

    def update_document(self, doc_id, loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai, so_to, ghi_chu, file_url):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE documents
            SET loai_ho_so = ?, so_va_ky_hieu = ?, ngay_thang = ?, ten_loai_trich_yeu_noi_dung = ?, so_to = ?, ghi_chu = ?, file_url = ?
            WHERE id = ?
        ''', (loai_ho_so, so_va_ky_hieu, ngay_thang, ten_loai, so_to, ghi_chu, file_url, doc_id))
        conn.commit()
        conn.close()

    def delete_document(self, doc_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
     # -----------------------
    # Work histories (Quá trình công tác) CRUD
    # -----------------------
    def add_work_history(self, staff_id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu):
        """
        Thêm bản ghi quá trình công tác cho staff_id.
        Các trường ngày có thể lưu dạng text 'YYYY-MM-DD' hoặc định dạng khác tuỳ bạn.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO work_histories (staff_id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (staff_id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu))
        conn.commit()
        conn.close()

    def get_work_histories_by_staff(self, staff_id):
        """
        Trả về tất cả bản ghi work_histories của 1 nhân viên (staff_id).
        Kết quả: list các tuple (id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu)
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu
            FROM work_histories
            WHERE staff_id = ?
            ORDER BY id DESC
        ''', (staff_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_all_work_histories(self):
        """
        Trả về tất cả work histories, kèm tên nhân viên và id nhân viên để hiển thị ở view chung.
        Kết quả: (wh.id, s.full_name, wh.decision_no, wh.ngay_quyet_dinh, ...)
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT wh.id, s.full_name, wh.decision_no, wh.ngay_quyet_dinh, wh.cac_vi_tri_cong_tac, wh.giu_chuc_vu, wh.cong_tac_tai_cq, wh.ghi_chu, wh.staff_id
            FROM work_histories wh
            LEFT JOIN staffs s ON wh.staff_id = s.id
            ORDER BY wh.id DESC
        ''')
        rows = cur.fetchall()
        conn.close()
        return rows

    def update_work_history(self, wh_id, decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE work_histories
            SET decision_no = ?, ngay_quyet_dinh = ?, cac_vi_tri_cong_tac = ?, giu_chuc_vu = ?, cong_tac_tai_cq = ?, ghi_chu = ?
            WHERE id = ?
        ''', (decision_no, ngay_quyet_dinh, cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu, wh_id))
        conn.commit()
        conn.close()

    def delete_work_history(self, wh_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM work_histories WHERE id = ?", (wh_id,))
        conn.commit()
        conn.close()

    # -----------------------
    # Statistics
    # -----------------------
    def get_statistics(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM departments")
        dept_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM staffs")
        staff_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM staff_awards")
        award_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documents")
        doc_count = cur.fetchone()[0]
        conn.close()
        return dept_count, staff_count, award_count, doc_count
    
    # -----------------------
    # Sample Data Ensurance
    # -----------------------
    def _ensure_complete_sample_data(self):
        """Thêm dữ liệu mẫu đầy đủ cho tất cả các bảng"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        # 1. Kiểm tra và thêm Departments
        cur.execute("SELECT COUNT(*) FROM departments")
        if cur.fetchone()[0] == 0:
            departments = [
                ("Phòng Công nghệ thông tin", "Quản lý hệ thống và phát triển phần mềm"),
                ("Phòng Nhân sự", "Quản lý nhân sự và tuyển dụng"),
                ("Phòng Kế toán", "Quản lý tài chính và kế toán"),
                ("Phòng Hành chính", "Quản lý hành chính tổng hợp"),
                ("Phòng Kinh doanh", "Phát triển kinh doanh và chăm sóc khách hàng"),
            ]
            cur.executemany("INSERT INTO departments (name, description) VALUES (?, ?)", departments)
            print("✓ Đã thêm 5 phòng ban mẫu")

        # 2. Kiểm tra và thêm Award Years
        cur.execute("SELECT COUNT(*) FROM award_years")
        if cur.fetchone()[0] == 0:
            years = [(2020,), (2021,), (2022,), (2023,), (2024,), (2025,)]
            cur.executemany("INSERT INTO award_years (year) VALUES (?)", years)
            print("✓ Đã thêm năm khen thưởng 2020-2025")

        # 3. Kiểm tra và thêm Award Authorities
        cur.execute("SELECT COUNT(*) FROM award_authorities")
        if cur.fetchone()[0] == 0:
            authorities = [
                ("UBND Thành phố",),
                ("Sở Nội vụ",),
                ("Ban Tổ chức Tỉnh ủy",),
                ("Bộ Nội vụ",),
                ("Thủ tướng Chính phủ",),
            ]
            cur.executemany("INSERT INTO award_authorities (name) VALUES (?)", authorities)
            print("✓ Đã thêm 5 cơ quan ban hành")

        # 4. Kiểm tra và thêm Award Titles
        cur.execute("SELECT COUNT(*) FROM award_titles")
        if cur.fetchone()[0] == 0:
            titles = [
                # Cá nhân - Cơ sở
                ("Lao động tiên tiến", "ca_nhan", "co_so"),
                ("Chiến sĩ thi đua cơ sở", "ca_nhan", "co_so"),
                ("Hoàn thành xuất sắc nhiệm vụ", "ca_nhan", "co_so"),
                # Cá nhân - Tỉnh
                ("Chiến sĩ thi đua cấp tỉnh", "ca_nhan", "tinh"),
                ("Bằng khen UBND Tỉnh", "ca_nhan", "tinh"),
                # Cá nhân - Trung ương
                ("Chiến sĩ thi đua toàn quốc", "ca_nhan", "trung_uong"),
                ("Huân chương Lao động hạng Ba", "ca_nhan", "trung_uong"),
                ("Bằng khen Thủ tướng Chính phủ", "ca_nhan", "trung_uong"),
                # Tập thể - Cơ sở
                ("Tập thể lao động tiên tiến", "tap_the", "co_so"),
                ("Tập thể xuất sắc", "tap_the", "co_so"),
                # Tập thể - Tỉnh
                ("Cờ thi đua cấp tỉnh", "tap_the", "tinh"),
                ("Bằng khen UBND Tỉnh (Tập thể)", "tap_the", "tinh"),
                # Tập thể - Trung ương
                ("Cờ thi đua của Chính phủ", "tap_the", "trung_uong"),
                ("Huân chương Lao động hạng Ba (Tập thể)", "tap_the", "trung_uong"),
            ]
            cur.executemany("INSERT INTO award_titles (name, scope, level) VALUES (?, ?, ?)", titles)
            print("✓ Đã thêm 14 danh hiệu khen thưởng")

        conn.commit()

        # 5. Kiểm tra và thêm Staffs
        cur.execute("SELECT COUNT(*) FROM staffs")
        if cur.fetchone()[0] == 0:
            # Lấy danh sách department_id
            cur.execute("SELECT id FROM departments ORDER BY id")
            dept_ids = [row[0] for row in cur.fetchall()]
            
            staff_data = [
                # Phòng IT (dept 1)
                (1, "Nguyễn Văn An", "1985-03-15", "Trưởng phòng", "0901234567", dept_ids[0]),
                (2, "Trần Thị Bích", "1990-07-22", "Lập trình viên", "0902345678", dept_ids[0]),
                (3, "Lê Văn Cường", "1992-11-08", "Lập trình viên", "0903456789", dept_ids[0]),
                (4, "Phạm Thị Dung", "1988-05-12", "System Admin", "0904567890", dept_ids[0]),
                # Phòng Nhân sự (dept 2)
                (1, "Hoàng Văn Em", "1987-09-25", "Trưởng phòng", "0905678901", dept_ids[1]),
                (2, "Đỗ Thị Phượng", "1991-02-14", "Chuyên viên", "0906789012", dept_ids[1]),
                (3, "Vũ Văn Giang", "1993-06-30", "Chuyên viên", "0907890123", dept_ids[1]),
                # Phòng Kế toán (dept 3)
                (1, "Ngô Thị Hoa", "1986-12-05", "Trưởng phòng", "0908901234", dept_ids[2]),
                (2, "Bùi Văn Ích", "1989-08-18", "Kế toán trưởng", "0909012345", dept_ids[2]),
                (3, "Đinh Thị Kim", "1994-04-27", "Kế toán viên", "0900123456", dept_ids[2]),
                # Phòng Hành chính (dept 4)
                (1, "Trương Văn Long", "1984-10-11", "Trưởng phòng", "0911234567", dept_ids[3]),
                (2, "Phan Thị Mai", "1992-01-20", "Văn thư", "0912345678", dept_ids[3]),
                # Phòng Kinh doanh (dept 5)
                (1, "Lý Văn Nam", "1988-07-09", "Trưởng phòng", "0913456789", dept_ids[4]),
                (2, "Cao Thị Oanh", "1991-03-16", "Nhân viên kinh doanh", "0914567890", dept_ids[4]),
                (3, "Đặng Văn Phúc", "1995-09-23", "Nhân viên kinh doanh", "0915678901", dept_ids[4]),
            ]
            
            cur.executemany('''
                INSERT INTO staffs (stt, full_name, dob, position, phone, department_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', staff_data)
            print("✓ Đã thêm 15 nhân viên mẫu")

        conn.commit()

        # 6. Kiểm tra và thêm Award Batches
        cur.execute("SELECT COUNT(*) FROM award_batches")
        if cur.fetchone()[0] == 0:
            # Lấy IDs
            cur.execute("SELECT id FROM award_years ORDER BY year DESC")
            year_ids = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT id FROM award_titles")
            title_ids = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT id FROM award_authorities")
            auth_ids = [row[0] for row in cur.fetchall()]
            
            # Tạo các đợt khen thưởng (20 đợt)
            batches = []
            for i in range(20):
                year_id = random.choice(year_ids)
                title_id = random.choice(title_ids)
                auth_id = random.choice(auth_ids)
                
                # Tạo ngày quyết định ngẫu nhiên
                base_date = datetime(2020, 1, 1)
                random_days = random.randint(0, 1825)  # 5 years
                decision_date = (base_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
                
                decision_no = f"QD-{1000 + i}/2024"
                note = f"Đợt khen thưởng lần {i+1}"
                
                batches.append((year_id, title_id, auth_id, decision_no, decision_date, note))
            
            cur.executemany('''
                INSERT INTO award_batches (award_year_id, award_title_id, authority_id, decision_no, decision_date, note)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', batches)
            print("✓ Đã thêm 20 đợt khen thưởng")

        conn.commit()

        # 7. Kiểm tra và thêm Staff Awards
        cur.execute("SELECT COUNT(*) FROM staff_awards")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id FROM staffs")
            staff_ids = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT id FROM award_batches")
            batch_ids = [row[0] for row in cur.fetchall()]
            
            # Tạo 30 khen thưởng cá nhân ngẫu nhiên
            staff_awards = []
            for _ in range(30):
                staff_id = random.choice(staff_ids)
                batch_id = random.choice(batch_ids)
                note = random.choice([
                    "Hoàn thành xuất sắc nhiệm vụ",
                    "Có nhiều đóng góp cho đơn vị",
                    "Gương mẫu, tận tụy",
                    "",
                ])
                staff_awards.append((staff_id, batch_id, note))
            
            cur.executemany('''
                INSERT INTO staff_awards (staff_id, award_batch_id, note)
                VALUES (?, ?, ?)
            ''', staff_awards)
            print("✓ Đã thêm 30 khen thưởng cá nhân")

        conn.commit()

        # 8. Kiểm tra và thêm Department Awards
        cur.execute("SELECT COUNT(*) FROM department_awards")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id FROM departments")
            dept_ids = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT id FROM award_batches")
            batch_ids = [row[0] for row in cur.fetchall()]
            
            # Tạo 15 khen thưởng tập thể
            dept_awards = []
            for _ in range(15):
                dept_id = random.choice(dept_ids)
                batch_id = random.choice(batch_ids)
                note = random.choice([
                    "Tập thể hoàn thành xuất sắc nhiệm vụ năm",
                    "Đơn vị dẫn đầu phong trào thi đua",
                    "Có nhiều thành tích nổi bật",
                    "",
                ])
                dept_awards.append((dept_id, batch_id, note))
            
            cur.executemany('''
                INSERT INTO department_awards (department_id, award_batch_id, note)
                VALUES (?, ?, ?)
            ''', dept_awards)
            print("✓ Đã thêm 15 khen thưởng tập thể")

        conn.commit()

        # 9. Kiểm tra và thêm Documents
        cur.execute("SELECT COUNT(*) FROM documents")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id FROM staffs")
            staff_ids = [row[0] for row in cur.fetchall()]
            
            loai_ho_so_list = ["Hợp đồng", "Quyết định", "Văn bằng", "Chứng chỉ", "Sơ yếu lý lịch"]
            
            docs = []
            for i, staff_id in enumerate(staff_ids[:10]):  # 10 nhân viên đầu
                for j in range(2):  # Mỗi người 2 tài liệu
                    loai = random.choice(loai_ho_so_list)
                    so_ky_hieu = f"SV-{100+i*10+j}"
                    ngay_thang = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                    ten_loai = f"Tài liệu {loai}"
                    so_to = random.randint(1, 10)
                    ghi_chu = f"Ghi chú cho {loai}"
                    file_url = f"/files/doc_{i}_{j}.pdf"
                    
                    docs.append((staff_id, loai, so_ky_hieu, ngay_thang, ten_loai, so_to, ghi_chu, file_url))
            
            cur.executemany('''
                INSERT INTO documents (staff_id, loai_ho_so, so_va_ky_hieu, ngay_thang, 
                                      ten_loai_trich_yeu_noi_dung, so_to, ghi_chu, file_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', docs)
            print("✓ Đã thêm 20 tài liệu mẫu")

        conn.commit()

        # 10. Kiểm tra và thêm Work Histories
        cur.execute("SELECT COUNT(*) FROM work_histories")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id FROM staffs")
            staff_ids = [row[0] for row in cur.fetchall()]
            
            histories = []
            positions = ["Nhân viên", "Chuyên viên", "Trưởng phòng phó", "Trưởng phòng"]
            
            for staff_id in staff_ids[:8]:  # 8 nhân viên đầu
                for k in range(2):  # Mỗi người 2 quá trình
                    decision_no = f"QĐ-{200+staff_id*10+k}/2024"
                    ngay_qd = f"202{random.randint(0,4)}-{random.randint(1,12):02d}-01"
                    vi_tri = random.choice(positions)
                    giu_chuc = f"202{random.randint(0,4)}-{random.randint(1,12):02d}-01"
                    cong_tac = f"202{random.randint(0,4)}-{random.randint(1,12):02d}-01"
                    ghi_chu = f"Bổ nhiệm {vi_tri}"
                    
                    histories.append((staff_id, decision_no, ngay_qd, vi_tri, giu_chuc, cong_tac, ghi_chu))
            
            cur.executemany('''
                INSERT INTO work_histories (staff_id, decision_no, ngay_quyet_dinh, 
                                           cac_vi_tri_cong_tac, giu_chuc_vu, cong_tac_tai_cq, ghi_chu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', histories)
            print("✓ Đã thêm 16 quá trình công tác")

        conn.commit()
        conn.close()
        print("=" * 60)
        print("✓ HOÀN TẤT: Đã thêm đầy đủ dữ liệu mẫu vào database")
        print("=" * 60)

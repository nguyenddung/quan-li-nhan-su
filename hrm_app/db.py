# hrm_app/db.py
# Database layer (cập nhật): tự động gán STT cho nhân viên theo phòng ban,
# và resequence STT khi xóa nhân viên.

import sqlite3

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

        # award_years
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER UNIQUE NOT NULL
            )
        ''')

        # award_titles
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                scope TEXT
            )
        ''')

        # award_batches
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                award_year_id INTEGER NOT NULL,
                award_title_id INTEGER NOT NULL,
                decision_no TEXT,
                decision_date DATE,
                note TEXT,
                FOREIGN KEY (award_year_id) REFERENCES award_years(id) ON DELETE CASCADE,
                FOREIGN KEY (award_title_id) REFERENCES award_titles(id) ON DELETE CASCADE
            )
        ''')

        # staff_awards
        cur.execute('''
            CREATE TABLE IF NOT EXISTS staff_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                award_batch_id INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY (staff_id) REFERENCES staffs(id) ON DELETE CASCADE,
                FOREIGN KEY (award_batch_id) REFERENCES award_batches(id) ON DELETE CASCADE
            )
        ''')

        # department_awards
        cur.execute('''
            CREATE TABLE IF NOT EXISTS department_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL,
                award_batch_id INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
                FOREIGN KEY (award_batch_id) REFERENCES award_batches(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()
        self.add_sample_data()

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
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM award_titles ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_award_title(self, name, scope):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO award_titles (name, scope) VALUES (?, ?)", (name, scope))
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
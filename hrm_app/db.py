"""
db.py
Database layer: DatabaseManager dùng sqlite3.
Tách riêng để dễ test và sửa lỗi liên quan DB.
"""
import sqlite3

class DatabaseManager:
    """
    Quản lý DB sqlite:
    - Tạo file DB (mặc định hrm_ultimate.db)
    - Tạo schema nếu chưa tồn tại
    - Cung cấp CRUD cơ bản cho modules GUI
    """
    def __init__(self, db_name="hrm_ultimate.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        # Bật foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_database(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # departments
        cur.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY ,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')

        # staffs
        cur.execute('''
            CREATE TABLE IF NOT EXISTS staffs (
                id INTEGER PRIMARY KEY ,
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
                id INTEGER PRIMARY KEY,
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
                id INTEGER PRIMARY KEY,
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
                id INTEGER PRIMARY KEY,
                year INTEGER UNIQUE NOT NULL
            )
        ''')

        # award_titles
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_titles (
                id INTEGER PRIMARY KEY ,
                name TEXT NOT NULL,
                scope TEXT
            )
        ''')

        # award_batches
        cur.execute('''
            CREATE TABLE IF NOT EXISTS award_batches (
                id INTEGER PRIMARY KEY ,
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
                id INTEGER PRIMARY KEY,
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
                id INTEGER PRIMARY KEY ,
                department_id INTEGER NOT NULL,
                award_batch_id INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
                FOREIGN KEY (award_batch_id) REFERENCES award_batches(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

        # Thêm dữ liệu mẫu nếu cần
        self.add_sample_data()

    def add_sample_data(self):
        """Thêm dữ liệu mẫu để giao diện không trống khi chạy lần đầu"""
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

            cur.execute("INSERT INTO staffs (stt, full_name, position, phone, department_id) VALUES (1, 'Nguyễn Văn A', 'Giám đốc CNTT', '0904555111', 1)")
            cur.execute("INSERT INTO staffs (stt, full_name, position, phone, department_id) VALUES (2, 'Trần Thị B', 'Trưởng phòng Nhân sự', '0904555222', 2)")

            cur.execute("INSERT INTO award_years (year) VALUES (2023)")
            cur.execute("INSERT INTO award_years (year) VALUES (2024)")

            cur.execute("INSERT INTO award_titles (name, scope) VALUES ('Chiến sĩ thi đua cơ sở', 'Cấp cơ sở')")
            cur.execute("INSERT INTO award_titles (name, scope) VALUES ('Lao động tiên tiến', 'Cấp cơ sở')")

            conn.commit()
        conn.close()

    # -----------------------
    # CRUD Methods (tương tự mã gốc)
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

    def add_staff(self, stt, full_name, dob, position, phone, department_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO staffs (stt, full_name, dob, position, phone, department_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (stt, full_name, dob, position, phone, department_id))
        conn.commit()
        conn.close()

    def update_staff(self, staff_id, stt, full_name, dob, position, phone, department_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE staffs SET stt=?, full_name=?, dob=?, position=?, phone=?, department_id=?
            WHERE id=?
        ''', (stt, full_name, dob, position, phone, department_id, staff_id))
        conn.commit()
        conn.close()

    def delete_staff(self, staff_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM staffs WHERE id=?", (staff_id,))
        conn.commit()
        conn.close()

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
        """Cập nhật thông tin tài liệu theo id"""
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
        """Xóa tài liệu theo id"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()

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
    
    ### VIEW 
    def get_staffs_by_department(self, department_id):
        """Trả về list nhân viên thuộc department_id"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT s.id, s.stt, s.full_name, s.position, s.phone, s.dob, d.name
            FROM staffs s
            LEFT JOIN departments d ON s.department_id = d.id
            WHERE s.department_id = ?
            ORDER BY s.id
        ''', (department_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def search_staffs_by_name(self, query):
        """Tìm nhân sự theo tên (LIKE, không phân biệt hoa thường)"""
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
    
    def get_documents_by_staff(self, staff_id):
        """Lấy tất cả tài liệu của một nhân viên (theo staff_id)"""
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
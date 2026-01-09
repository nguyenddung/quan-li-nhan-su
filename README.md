````markdown
# HRM ULTIMATE - Modularized Project

Mục tiêu:
- Tách code lớn thành các module nhỏ để dễ debug, maintain và mở rộng.
- Giữ nguyên các chức năng: quản lý phòng ban, nhân sự, danh hiệu/năm, hồ sơ tài liệu, dashboard.
- Hỗ trợ vai trò admin (is_admin=True) để cho phép thêm/sửa/xóa.

Cấu trúc:
- main.py - entrypoint
- hrm_app/
  - __init__.py
  - db.py - DatabaseManager: tạo database, CRUD
  - dialogs.py - các helper dialog, center_window, wrappers cho messagebox
  - gui.py - HRMApp: layout chính, sidebar, header, quản lý việc hiển thị views
  - views/
    - __init__.py
    - dashboard.py - Dashboard view (thống kê + chart)
    - departments.py - Quản lý phòng ban (list, add, edit, delete)
    - staff.py - Quản lý nhân sự (list, add, edit, delete)
    - awards.py - Quản lý danh hiệu & năm (list, add)
    - documents.py - Quản lý hồ sơ (list, add)

Cài đặt:
1. Cài dependencies:
   pip install -r requirements.txt

   Lưu ý: `tkinter` và `sqlite3` là built-in trên hầu hết Python; nếu bạn dùng Linux và thiếu tkinter, cài gói hệ thống (ví dụ `sudo apt install python3-tk` trên Debian/Ubuntu).

2. Chạy:
   python main.py

Ghi chú:
- Database mặc định: `hrm_ultimate.db` tạo tự động nếu chưa có.
- Quyền admin (is_admin) mặc định bật; bạn có thể tắt để test chế độ chỉ xem.
- Mỗi view là 1 class riêng, dễ tách test và debug.
- Mã đã được comment tiếng Việt để bạn dễ hiểu logic từng phần.
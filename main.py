"""
main.py
Entry point: tạo và chạy HRMApp
"""
from hrm_app.gui import HRMApp

if __name__ == "__main__":
    # is_admin=True cho phép thêm/sửa/xóa. Đặt False nếu bạn muốn chỉ chế độ xem.
    app = HRMApp(is_admin=True)
    app.mainloop()
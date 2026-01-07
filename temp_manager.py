import tempfile
import os

def create_temp_file(suffix=".xlsx"):
    """Tạo file tạm để xử lý."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path

def delete_temp_file(path):
    """Xóa file tạm."""
    if os.path.exists(path):
        os.remove(path)

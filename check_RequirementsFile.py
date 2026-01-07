import importlib
import subprocess
import sys
import os

from logger import log  # dùng log() nhưng vẫn an toàn vì logger có fallback


def install_missing(requirements_file="requirements.txt", log_file="installed.log"):
    """
    Đọc requirements.txt, cài các package còn thiếu.
    Dùng log() để ghi log (ra console hoặc UI nếu có).
    """
    if not os.path.exists(requirements_file):
        log(f"⚠ Không tìm thấy {requirements_file}")
        return

    with open(requirements_file, encoding="utf-8") as f:
        packages = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

    for package in packages:
        pkg_name = package.split("==")[0]

        try:
            importlib.import_module(pkg_name)
            log(f"✔ {package} đã có sẵn")
        except ImportError:
            log(f"➜ Đang cài đặt {package} ...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                log(f"✔ Cài xong {package}")
            except Exception as e:
                log(f"❌ Không thể cài {package}: {e}")
                continue

            # Xử lý đặc biệt cho pywin32 nếu bạn muốn (tùy chọn)
            if pkg_name.lower() == "pywin32":
                try:
                    import site
                    site_packages = site.getsitepackages()[0]
                    postinstall = os.path.join(
                        site_packages, "pywin32_system32", "pywin32_postinstall.py"
                    )
                    if os.path.exists(postinstall):
                        log("🔧 Đang chạy pywin32_postinstall.py ...")
                        subprocess.check_call(
                            [sys.executable, postinstall, "-install"]
                        )
                        log("✔ Đã chạy postinstall cho pywin32")
                    else:
                        log("⚠ Không tìm thấy pywin32_postinstall.py")
                except Exception as e:
                    log(f"⚠ Lỗi khi chạy postinstall pywin32: {e}")

        # Ghi lại package đã xử lý
        try:
            with open(log_file, "a", encoding="utf-8") as lf:
                lf.write(f"{package}\n")
        except Exception:
            # Không cần crash nếu không ghi được log file
            pass
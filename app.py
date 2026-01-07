import streamlit as st

from logger import init_logger, log

import setup
from workflow import run_workflow


def main():
    st.set_page_config(page_title="Excel Combine Tool", layout="wide")

    st.title("🧩 Excel Combine Tool")

    # Khởi tạo logger để mọi log hiển thị lên web
    init_logger()
    log("🚀 Bắt đầu khởi tạo ứng dụng...")

    # Khởi tạo môi trường (cài package nếu thiếu)
    log("🔧 Đang kiểm tra và cài đặt các thư viện cần thiết...")
    setup.init_environment()
    log("✔ Môi trường đã sẵn sàng.")

    # Vùng UI chính của bạn (upload file, chọn option, chạy workflow, ...)
    st.markdown("---")
    log("📂 Sẵn sàng nhận dữ liệu đầu vào.")

    # Gọi workflow chính
    try:
        run_workflow()
        log("✅ Workflow đã chạy xong.")
    except Exception as e:
        log(f"❌ Lỗi trong workflow: {e}")
        st.error("Đã xảy ra lỗi khi chạy workflow. Vui lòng xem log ở phía trên.")


if __name__ == "__main__":
    main()
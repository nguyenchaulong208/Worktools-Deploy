@echo off
REM Lấy thư mục hiện tại của file BAT
cd /d "%~dp0"

echo Đang chạy ứng dụng Streamlit...

REM Nếu tồn tại môi trường ảo .venv thì dùng Python trong đó
if exist ".venv\Scripts\python.exe" (
    echo Đang sử dụng Python trong môi trường ảo .venv
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    echo Không tìm thấy môi trường ảo. Đang sử dụng Python hệ thống...
    python -m streamlit run app.py
)

pause

import pandas as pd
from io import BytesIO
import streamlit as st
import subprocess
import sys
import site
import os
import datetime
import time

from logger import log   # <--- TÍCH HỢP LOG

def run_workflow():
    log("▶ Bắt đầu workflow...")


def normalize_value(v):
    if isinstance(v, datetime.time):
        return v.strftime("%H:%M")
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, datetime.date):
        return v.strftime("%Y-%m-%d")
    return v


def ensure_pywin32():
    try:
        import win32com.client
        import pythoncom
        log("✔ pywin32 đã có sẵn")
        return True
    except ImportError:
        log("🔧 pywin32 chưa có, đang cài đặt...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        log("✔ Cài đặt pywin32 thành công")
    except Exception as e:
        log(f"❌ Không thể cài pywin32: {e}")
        return False

    try:
        site_packages = site.getsitepackages()[0]
        postinstall = os.path.join(site_packages, "pywin32_system32", "pywin32_postinstall.py")

        if os.path.exists(postinstall):
            log("🔧 Đang chạy postinstall...")
            subprocess.check_call([sys.executable, postinstall, "-install"])
            log("✔ Hoàn tất postinstall")
    except Exception as e:
        log(f"⚠ Lỗi khi chạy postinstall: {e}")

    try:
        import win32com.client
        import pythoncom
        log("✔ pywin32 đã sẵn sàng")
        return True
    except ImportError:
        log("❌ Không thể import win32com sau khi cài")
        return False


def save_with_form_dynamic_by_index(
    merged,
    form_file,
    output_name,
    sheet_name,
    start_row,
    end_row,
    body_start_col=1
):
    if not ensure_pywin32():
        log("❌ Không thể khởi tạo pywin32. Dừng xử lý.")
        return

    import win32com.client as win32
    import pythoncom

    pythoncom.CoInitialize()

    merged = merged.fillna("")
    body_data = merged.values.tolist()
    rows_needed = len(body_data)

    start_row = int(start_row)
    end_row = int(end_row)
    region_size = end_row - start_row + 1

    temp_path = os.path.join(os.getcwd(), f"_temp_form_{int(time.time())}.xlsx")
    with open(temp_path, "wb") as f:
        f.write(form_file.getvalue())

    save_path = os.path.join(os.getcwd(), output_name)

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    wb = None

    try:
        log("📄 Đang mở file Excel mẫu...")
        wb = excel.Workbooks.Open(temp_path)
        ws = wb.Worksheets(sheet_name)

        log("🧹 Xóa dữ liệu cũ trong vùng body...")
        ws.Range(
            ws.Cells(start_row, 1),
            ws.Cells(end_row, ws.UsedRange.Columns.Count)
        ).ClearContents()

        if rows_needed > region_size:
            rows_to_add = rows_needed - region_size
            insert_at = start_row + 1
            log(f"➕ Chèn thêm {rows_to_add} dòng...")
            ws.Rows(f"{insert_at}:{insert_at + rows_to_add - 1}").Insert()

        log("✍️ Đang ghi dữ liệu vào form...")
        for i, row_values in enumerate(body_data):
            for j, value in enumerate(row_values):
                ws.Cells(start_row + i, body_start_col + j).Value = normalize_value(value)

        log("💾 Đang lưu file kết quả...")
        wb.SaveAs(save_path)
        log("✔ Lưu file thành công!")

    except Exception as e:
        log(f"❌ Lỗi khi gộp: {e}")

    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=0)
        except:
            pass

        try:
            excel.Quit()
        except:
            pass

        try:
            pythoncom.CoUninitialize()
        except:
            pass

        try:
            os.remove(temp_path)
        except:
            pass

    try:
        with open(save_path, "rb") as f:
            file_bytes = f.read()

        st.success(f"✔ Đã tạo file: {output_name}")

        st.download_button(
            label="📥 Tải file kết quả",
            data=file_bytes,
            file_name=output_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        log(f"❌ Không thể tải file: {e}")
        
    log("✅ Kết thúc workflow.")

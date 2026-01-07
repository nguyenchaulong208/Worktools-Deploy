# import pandas as pd
# from io import BytesIO

# def merge_selected(selections):
#     """
#     Gộp dữ liệu từ nhiều file Excel theo lựa chọn của người dùng.

#     Parameters
#     ----------
#     selections : list[dict]
#         Mỗi dict chứa:
#         {
#           "file": UploadedFile (Streamlit),
#           "sheets": list[str],       # danh sách sheet muốn gộp
#           "columns": list[str]|None, # cột muốn gộp (None = tất cả)
#           "start_row": int|None      # dòng bắt đầu gộp (None = từ đầu)
#         }

#     Returns
#     -------
#     merged : pd.DataFrame
#         DataFrame đã gộp từ các file/sheet hợp lệ.
#     """
#     dfs = []
#     for sel in selections:
#         f = sel["file"]
#         sheets = sel.get("sheets", [])
#         columns = sel.get("columns")
#         start_row = sel.get("start_row")

#         for sheet in sheets:
#             # Đọc dữ liệu từ UploadedFile
#             file_bytes = BytesIO(f.getvalue())
#             xls = pd.ExcelFile(file_bytes)

#             if sheet not in xls.sheet_names:
#                 # Bỏ qua nếu sheet không tồn tại
#                 continue

#             # Reset con trỏ để đọc lại
#             file_bytes.seek(0)
#             df = pd.read_excel(file_bytes, sheet_name=sheet)

#             # Nếu chọn dòng bắt đầu
#             if start_row is not None and start_row < len(df):
#                 df = df.iloc[start_row:]

#             # Nếu chọn cột
#             if columns:
#                 valid_cols = [c for c in columns if c in df.columns]
#                 df = df[valid_cols]

#             dfs.append(df)

#     if not dfs:
#         raise ValueError("Không có dữ liệu hợp lệ để gộp. Kiểm tra lại lựa chọn file/sheet/cột.")

#     merged = pd.concat(dfs, ignore_index=True)
#     return merged


# def save_file(df, output_path="merged_result.xlsx"):
#     """
#     Lưu DataFrame ra file Excel mới.

#     Parameters
#     ----------
#     df : pd.DataFrame
#         DataFrame cần lưu.
#     output_path : str
#         Tên file xuất ra.

#     Returns
#     -------
#     output_path : str
#         Đường dẫn file đã lưu.
#     """
#     df.to_excel(output_path, index=False)
#     return output_path

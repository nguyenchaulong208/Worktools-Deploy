import pandas as pd

def read_excel_file(file_path):
    """Đọc file Excel và trả về thông tin sheet."""
    xls = pd.ExcelFile(file_path)
    sheets_info = {}
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        sheets_info[sheet] = {
            "rows": df.shape[0],
            "cols": df.shape[1],
            "has_data": not df.empty
        }
    return sheets_info

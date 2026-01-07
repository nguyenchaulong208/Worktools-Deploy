import pandas as pd
from io import BytesIO

def get_sheets(uploaded_file):
    xls = pd.ExcelFile(BytesIO(uploaded_file.getvalue()))
    return xls.sheet_names

def preview_sheet(uploaded_file, sheet_name):
    df = pd.read_excel(BytesIO(uploaded_file.getvalue()), sheet_name=sheet_name)
    return df
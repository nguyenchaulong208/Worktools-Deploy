import pandas as pd

def merge_data(selections, session_state, file_preview):
    merged = pd.DataFrame()
    for sel in selections:
        df = session_state.get(sel["key"])
        if df is None:
            df = file_preview.preview_sheet(sel["file"], sel["sheet"])

        if sel["columns"]:
            df = df[sel["columns"]]

        # Bỏ dòng đầu tiên
        df = df.iloc[1:]

        # Áp dụng chọn dòng bắt đầu
        if sel["start_row"] > 1:
            df = df.iloc[sel["start_row"] - 1:]

        merged = pd.concat([merged, df], ignore_index=True)
    return merged
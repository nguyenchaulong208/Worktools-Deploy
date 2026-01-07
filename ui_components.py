import streamlit as st

def upload_files():
    return st.file_uploader("📂 Chọn file Excel", type=["xlsx"], accept_multiple_files=True)

def select_sheets(file, sheets):
    return st.multiselect(f"📑 Chọn sheet trong {file.name}", sheets, key=f"{file.name}_sheets")

def edit_dataframe(df, sheet, file):
    st.markdown(f"#### Sheet: {sheet}")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # Xoá cột
    cols = list(edited_df.columns)
    cols_to_drop = st.multiselect(
        f"🧹 Chọn cột muốn xoá khỏi {sheet}",
        cols,
        key=f"{file.name}_{sheet}_dropcols"
    )
    if cols_to_drop:
        edited_df = edited_df.drop(columns=cols_to_drop)
        st.warning(f"Đã xoá các cột: {', '.join(cols_to_drop)}")
        st.dataframe(edited_df)

    # Dòng bắt đầu gộp
    start_row = st.number_input(
        f"🔢 Gộp từ dòng số trong {sheet}:",
        min_value=1,
        value=1,
        key=f"{file.name}_{sheet}_start"
    )

    return edited_df, start_row
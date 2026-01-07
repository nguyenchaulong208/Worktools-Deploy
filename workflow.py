import streamlit as st
import file_preview
from ui_components import upload_files, select_sheets, edit_dataframe
from data_operations import merge_data
from form_handler import save_with_form_dynamic_by_index
import pandas as pd
from openpyxl import load_workbook
from logger import log

def run_workflow():
    uploaded_files = upload_files()

    if uploaded_files:
        st.markdown("### Thiết lập gộp dữ liệu")
        selections = []

        # Chọn file nguồn để gộp
        for f in uploaded_files:
            with st.expander(f"Thiết lập cho: {f.name}", expanded=False):
                sheets = file_preview.get_sheets(f)
                sheet_sel = select_sheets(f, sheets)

                if sheet_sel:
                    for sheet in sheet_sel:
                        df = file_preview.preview_sheet(f, sheet)
                        edited_df, start_row = edit_dataframe(df, sheet, f)

                        st.session_state[f"edited_{f.name}_{sheet}"] = edited_df

                        selections.append({
                            "file": f,
                            "sheet": sheet,
                            "columns": None,
                            "start_row": start_row,
                            "key": f"edited_{f.name}_{sheet}"
                        })

        st.markdown("---")
        st.markdown("### Gộp và xuất file")

        # Tên file xuất
        output_name = st.text_input("Tên file xuất (xlsx)", value="merged_result.xlsx")

        # Chọn file form
        form_choice = st.selectbox("Chọn file làm form", [f.name for f in uploaded_files])
        form_file = next(f for f in uploaded_files if f.name == form_choice)

        # Chọn sheet form
        form_sheets = file_preview.get_sheets(form_file)
        form_sheet_choice = st.selectbox("Chọn sheet trong form", form_sheets)

        # -----------------------------
        # HIỂN THỊ FORM MẪU ĐỂ XEM TRƯỚC
        # -----------------------------
        st.markdown("### 📄 Xem trước form mẫu (để xác định dòng bắt đầu – kết thúc)")

        wb = load_workbook(form_file, data_only=True)
        ws = wb[form_sheet_choice]
        data = list(ws.values)
        df_form_preview = pd.DataFrame(data)
        df_form_preview.insert(0, "Dòng số", range(1, len(df_form_preview) + 1))
        st.dataframe(df_form_preview, height=500)

        st.info("👆 Hãy xem số dòng trong bảng trên rồi nhập dòng bắt đầu và kết thúc bên dưới")

        # Nhập vùng dữ liệu
        start_row = st.number_input("Dòng bắt đầu vùng dữ liệu", min_value=1, value=10)
        end_row = st.number_input("Dòng kết thúc vùng dữ liệu", min_value=start_row, value=start_row + 10)

        # Cột bắt đầu ghi dữ liệu
        body_start_col = st.number_input("Cột bắt đầu ghi dữ liệu", min_value=1, value=1)

        # -----------------------------
        # GỘP FILE
        # -----------------------------
        if st.button("Gộp file"):
            try:
                merged = merge_data(selections, st.session_state, file_preview)

                st.subheader("Kết quả gộp")
                st.dataframe(merged)

                save_with_form_dynamic_by_index(
                    merged=merged,
                    form_file=form_file,
                    output_name=output_name,
                    sheet_name=form_sheet_choice,
                    start_row=start_row,
                    end_row=end_row,
                    body_start_col=body_start_col
                )

            except Exception as e:
                st.error(f"❌ Lỗi khi gộp: {e}")
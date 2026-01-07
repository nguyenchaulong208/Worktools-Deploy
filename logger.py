import streamlit as st

_log_area = None
_logs = ""

def init_logger():
    global _log_area

    # Inject CSS + JS để tạo vùng log cố định và auto-scroll
    st.markdown("""
        <style>
        .log-box {
            background-color: #f9f9f9;
            border: 1px solid #ccc;
            padding: 10px;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
            overflow-y: auto;
            height: 300px;
        }
        </style>
        <script>
        function scrollLogBox() {
            var logBox = document.getElementById("log-box");
            if (logBox) {
                logBox.scrollTop = logBox.scrollHeight;
            }
        }
        </script>
    """, unsafe_allow_html=True)

    _log_area = st.empty()
    _log_area.markdown('<div class="log-box" id="log-box"></div>', unsafe_allow_html=True)

def log(msg):
    global _logs, _log_area
    _logs += str(msg) + "\n"

    if _log_area is not None:
        # Cập nhật nội dung log + gọi JS để cuộn xuống
        _log_area.markdown(
            f'''
            <div class="log-box" id="log-box">{_logs}</div>
            <script>scrollLogBox();</script>
            ''',
            unsafe_allow_html=True
        )
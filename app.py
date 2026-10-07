import streamlit as st
import requests
import urllib.parse
import re

# Cấu hình trang
st.set_page_config(page_title="Tìm Vần Tiếng Việt", page_icon="🔍")
st.title("🔍 Tra Cứu Vần Tiếng Việt")

# Ô nhập từ trên web
tu_khoa = st.text_input("Nhập từ cần tìm (ví dụ: trong veo):", "")

def tim_van(tu):
    query_encoded = urllib.parse.quote_plus(tu)
    url = f"https://vuatiengviet.vn/?query={query_encoded}&_rsc=8kzk2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "RSC": "1",
        "Referer": "https://vuatiengviet.vn/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8' # Đảm bảo không lỗi font
        pattern = r'"className":"leading-tight","children":"([^"]+)"'
        ket_qua = re.findall(pattern, response.text)
        return list(dict.fromkeys(ket_qua))
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return []

# Bấm nút hoặc nhấn Enter
if st.button("Tìm kiếm") or tu_khoa:
    if tu_khoa.strip():
        with st.spinner("Đang tìm dữ liệu..."):
            danh_sach = tim_van(tu_khoa.strip())
            
        if danh_sach:
            st.success(f"Tìm thấy {len(danh_sach)} kết quả:")
            for i, tu in enumerate(danh_sach, 1):
                st.write(f"**{i}.** {tu}")
        else:
            st.warning("Không tìm thấy kết quả phù hợp.")

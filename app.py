import html
import re
import unicodedata

import requests
import streamlit as st


st.set_page_config(page_title="Tìm Vần", page_icon="🔎", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background: #f5f7fb; }
    .block-container { max-width: 820px; padding-top: 3rem; }
    .hero { text-align: center; margin-bottom: 1.8rem; }
    .hero h1 { color: #18243b; font-size: 2.35rem; margin-bottom: .35rem; }
    .hero p { color: #667085; font-size: 1rem; margin: 0; }
    div.stButton > button { width: 100%; border-radius: 12px; min-height: 46px;
        background: #315efb; color: white; border: 0; font-weight: 650; }
    div.stButton > button:hover { background: #244bd4; color: white; }
    .result-card { background: white; border: 1px solid #e6eaf2; border-radius: 12px;
        padding: 13px 16px; color: #18243b; font-size: 1.05rem;
        box-shadow: 0 2px 8px rgba(20, 35, 70, .04); }
    .results-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 10px; margin-top: 12px; }
    @media (max-width: 700px) {
        .results-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
        .result-card { padding: 8px 6px; font-size: .88rem; line-height: 1.2;
            border-radius: 8px; overflow-wrap: anywhere; }
    }
    @media (max-width: 380px) {
        .results-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px; }
        .result-card { padding: 7px 5px; font-size: .82rem; }
    }
    .loader-wrap { display: flex; justify-content: center; padding: 22px; }
    .loader { width: 28px; height: 28px; border: 3px solid #dce4ff;
        border-top-color: #315efb; border-radius: 50%; animation: spin .75s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    </style>
    <div class="hero">
      <h1>Tìm Vần</h1>
      <p>Tra cứu vần xuôi và lọc kết quả theo thanh điệu</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def thanh_dieu(tu):
    decomposed = unicodedata.normalize("NFD", tu.lower())
    marks = {
        "\u0301": "sắc",
        "\u0300": "huyền",
        "\u0303": "ngã",
        "\u0309": "hỏi",
        "\u0323": "nặng",
    }
    found = set(decomposed) & set(marks)
    return marks[next(iter(found))] if found else "ngang"


def loc_theo_thanh_dieu(danh_sach, tu_khoa):
    thanh_can_tim = [thanh_dieu(tieng) for tieng in tu_khoa.split()]
    ket_qua = []
    for ung_vien in danh_sach:
        cac_tieng = ung_vien.split()
        if len(cac_tieng) >= len(thanh_can_tim) and all(
            thanh_dieu(cac_tieng[i]) == thanh
            for i, thanh in enumerate(thanh_can_tim)
        ):
            ket_qua.append(ung_vien)
    return ket_qua


def tim_van_xuoi(tu_khoa, cap_nhat):
    url = "https://vuatiengviet.vn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "RSC": "1",
        "Referer": url,
    }
    pattern = r'"className":"leading-tight","children":"([^"]+)"'
    ket_qua = []
    da_gap = set()

    for trang in range(1, 101):
        response = requests.get(
            url,
            params={
                "query": tu_khoa,
                "type": "van-xuoi",
                "page": trang,
                "_rsc": "8kzk2",
            },
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        ket_qua_trang = re.findall(pattern, response.text)
        if not ket_qua_trang:
            break

        for tu in loc_theo_thanh_dieu(ket_qua_trang, tu_khoa):
            if tu not in da_gap:
                da_gap.add(tu)
                ket_qua.append(tu)
        cap_nhat(ket_qua)

        if len(ket_qua_trang) < 20:
            break

    return ket_qua


with st.form("search_form"):
    tu_khoa = st.text_input(
        "Từ khóa",
        placeholder="Nhập từ hoặc cụm từ cần tìm...",
        label_visibility="collapsed",
    ).strip()
    tim_kiem = st.form_submit_button("Tìm vần xuôi")

if tim_kiem:
    if not tu_khoa:
        st.warning("Vui lòng nhập từ khóa.")
    else:
        spinner = st.empty()
        ket_qua_khu_vuc = st.empty()
        spinner.markdown(
            '<div class="loader-wrap"><div class="loader"></div></div>',
            unsafe_allow_html=True,
        )

        def cap_nhat(ket_qua):
            with ket_qua_khu_vuc.container():
                st.markdown(f"**{len(ket_qua)} kết quả**")
                cards = "".join(
                    f'<div class="result-card">{html.escape(tu)}</div>'
                    for tu in ket_qua
                )
                st.markdown(
                    f'<div class="results-grid">{cards}</div>',
                    unsafe_allow_html=True,
                )

        try:
            ket_qua = tim_van_xuoi(tu_khoa, cap_nhat)
            spinner.empty()
            if not ket_qua:
                ket_qua_khu_vuc.info("Không tìm thấy kết quả phù hợp.")
        except requests.RequestException:
            spinner.empty()
            ket_qua_khu_vuc.error(
                "Không thể kết nối để tải kết quả. Vui lòng thử lại."
            )

import html
import re
import unicodedata

import requests
import streamlit as st


st.set_page_config(page_title="Tìm Vần", page_icon="🔎", layout="centered")

st.session_state.setdefault("search_history", [])
st.session_state.setdefault("search_text", "")

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


def lay_ket_qua_noi_lai(tu_khoa):
    url = "https://vuatiengviet.vn/tim-van"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "RSC": "1",
        "Referer": "https://vuatiengviet.vn/tim-van?type=noi-lai",
    }
    response = requests.get(
        url,
        params={"query": tu_khoa, "type": "noi-lai", "_rsc": "8kzk2"},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    van_ban = response.text
    van_ban_thuong = van_ban.casefold()
    vi_tri_noi_lai = van_ban_thuong.find("nói lái")
    if vi_tri_noi_lai < 0:
        return []

    vi_tri_freestyle = van_ban_thuong.find("freestyle", vi_tri_noi_lai)
    if vi_tri_freestyle >= 0:
        van_ban = van_ban[vi_tri_noi_lai:vi_tri_freestyle]
    else:
        van_ban = van_ban[vi_tri_noi_lai:]

    pattern = r'"className":"leading-tight","children":"((?:\\.|[^"\\])*)"'
    ket_qua = []
    for noi_dung in re.findall(pattern, van_ban):
        tu = html.unescape(noi_dung.replace('\\"', '"').replace('\\n', ' ')).strip()
        if tu and tu not in ket_qua:
            ket_qua.append(tu)
    return ket_qua


def luu_lich_su(loai, tu_khoa, ket_qua):
    st.session_state.search_history.insert(
        0,
        {"loai": loai, "tu_khoa": tu_khoa, "ket_qua": list(ket_qua)},
    )
    del st.session_state.search_history[20:]


def tim_van_xuoi(tu_khoa, cap_nhat):
    url = "https://vuatiengviet.vn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "RSC": "1",
        "Referer": url,
    }
    pattern = r'"className":"leading-tight","children":"([^"]+)"'
    chi_lay_tieng_cuoi = len(tu_khoa.split()) == 1
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

        if chi_lay_tieng_cuoi:
            cac_tu_phu_hop = []
            for tu in ket_qua_trang:
                cac_tieng = tu.split()
                if cac_tieng and thanh_dieu(cac_tieng[-1]) == thanh_dieu(tu_khoa):
                    cac_tu_phu_hop.append(tu)
        else:
            cac_tu_phu_hop = loc_theo_thanh_dieu(ket_qua_trang, tu_khoa)

        for tu in cac_tu_phu_hop:
            hien_thi = tu.split()[-1] if chi_lay_tieng_cuoi else tu
            if hien_thi not in da_gap:
                da_gap.add(hien_thi)
                ket_qua.append(hien_thi)
        cap_nhat(ket_qua)

        if len(ket_qua_trang) < 20:
            break

    return ket_qua


if st.button("Xóa nhanh ô nhập", key="clear_search_text"):
    st.session_state.search_text = ""

with st.form("search_form"):
    tu_khoa = st.text_input(
        "Từ khóa",
        placeholder="Nhập từ hoặc cụm từ cần tìm...",
        label_visibility="collapsed",
        key="search_text",
    ).strip()
    nut_tim_kiem, nut_noi_lai = st.columns(2)
    tim_kiem = nut_tim_kiem.form_submit_button("Tìm vần xuôi")
    tim_noi_lai = nut_noi_lai.form_submit_button("Tìm nói lái")

if tim_noi_lai:
    if not tu_khoa:
        st.warning("Vui lòng nhập từ hoặc cụm từ cần tìm nói lái.")
    else:
        with st.spinner("Đang tìm nói lái trên Vựa Tiếng Việt..."):
            try:
                ket_qua_noi_lai = lay_ket_qua_noi_lai(tu_khoa)
                if ket_qua_noi_lai:
                    st.markdown(f"**{len(ket_qua_noi_lai)} kết quả nói lái**")
                    cards = "".join(
                        f'<div class="result-card">{html.escape(tu)}</div>'
                        for tu in ket_qua_noi_lai
                    )
                    st.markdown(
                        f'<div class="results-grid">{cards}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("Trang nguồn không trả về kết quả nói lái.")
                luu_lich_su("Nói lái", tu_khoa, ket_qua_noi_lai)
            except requests.RequestException:
                st.error("Không thể kết nối tới Vựa Tiếng Việt để tìm nói lái.")

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
            luu_lich_su("Tìm vần xuôi", tu_khoa, ket_qua)
            if not ket_qua:
                ket_qua_khu_vuc.info("Không tìm thấy kết quả phù hợp.")
        except requests.RequestException:
            spinner.empty()
            ket_qua_khu_vuc.error(
                "Không thể kết nối để tải kết quả. Vui lòng thử lại."
            )

with st.expander("Lịch sử tìm kiếm", expanded=False):
    if st.button("Xóa lịch sử", key="clear_search_history"):
        st.session_state.search_history.clear()

    if not st.session_state.search_history:
        st.caption("Chưa có lượt tìm kiếm nào trong phiên này.")
    else:
        for muc in st.session_state.search_history:
            st.text(f'{muc["loai"]}: {muc["tu_khoa"]}')
            st.caption(", ".join(muc["ket_qua"]) or "Không có kết quả")

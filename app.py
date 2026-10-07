import requests
import re
import sys
import unicodedata
import threading
import itertools

# Đảm bảo terminal in được tiếng Việt (đặc biệt trên Windows)
sys.stdout.reconfigure(encoding='utf-8')

def tim_van(tu_khoa):
    url = "https://vuatiengviet.vn/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "RSC": "1",
        "Referer": "https://vuatiengviet.vn/"
    }
    
    ket_qua_tat_ca = []
    da_in = set()
    try:
        
        # SỬA LỖI FONT CHỮ TẠI ĐÂY
        # Ép request đọc dữ liệu web bằng bảng mã UTF-8
        
        pattern = r'"className":"leading-tight","children":"([^"]+)"'
        cac_loai_tim_kiem = ("van-xuoi",)

        for loai in cac_loai_tim_kiem:
            for trang in range(1, 101):
                dang_tai = threading.Event()

                def hien_bieu_tuong_tai():
                    for ky_tu in itertools.cycle("|/-\\"):
                        if dang_tai.is_set():
                            break
                        sys.stdout.write("\r" + ky_tu)
                        sys.stdout.flush()
                        dang_tai.wait(0.1)

                luong_tai = threading.Thread(target=hien_bieu_tuong_tai, daemon=True)
                luong_tai.start()
                try:
                    response = requests.get(
                        url,
                        params={
                            "query": tu_khoa,
                            "type": loai,
                            "page": trang,
                            "_rsc": "8kzk2",
                        },
                        headers=headers,
                        timeout=20,
                    )
                finally:
                    dang_tai.set()
                    luong_tai.join()
                    sys.stdout.write("\r \r")
                    sys.stdout.flush()
                response.raise_for_status()
                response.encoding = "utf-8"
                ket_qua_trang = re.findall(pattern, response.text)
                if not ket_qua_trang:
                    break

                ket_qua_loc = loc_theo_thanh_dieu(ket_qua_trang, tu_khoa)
                moi = [tu for tu in ket_qua_loc if tu not in da_in]
                if moi:
                    for tu in moi:
                        print(f"- {tu}")
                        da_in.add(tu)
                        ket_qua_tat_ca.append(tu)

                if len(ket_qua_trang) < 20:
                    break

        return ket_qua_tat_ca

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi yêu cầu mạng: {e}")
        return ket_qua_tat_ca


def thanh_dieu(tu):
    """Trả về thanh điệu của một âm tiết (ngang, sắc, huyền, hỏi, ngã, nặng)."""
    decomposed = unicodedata.normalize("NFD", tu.lower())
    thanh_dieu_unicode = {
        "\u0301": "sắc",
        "\u0300": "huyền",
        "\u0303": "ngã",
        "\u0309": "hỏi",
        "\u0323": "nặng",
    }
    dau = set(decomposed) & set(thanh_dieu_unicode)
    return thanh_dieu_unicode[next(iter(dau))] if dau else "ngang"


def loc_theo_thanh_dieu(danh_sach, tu_khoa):
    """Lọc theo thanh điệu từng tiếng, đúng vị trí người dùng nhập."""
    tu_khoa_tieng = tu_khoa.split()
    thanh_dieu_can_tim = [thanh_dieu(tieng) for tieng in tu_khoa_tieng]

    ket_qua = []
    for ung_vien in danh_sach:
        cac_tieng = ung_vien.split()
        if len(cac_tieng) < len(thanh_dieu_can_tim):
            continue
        if all(thanh_dieu(cac_tieng[i]) == thanh for i, thanh in enumerate(thanh_dieu_can_tim)):
            ket_qua.append(ung_vien)
    return ket_qua

if __name__ == "__main__":
    print("="*40)
    print("   CÔNG CỤ TÌM VẦN - VUATIENGVIET.VN")
    print("="*40)
    
    while True:
        tu_nhap_vao = input("\nNhập từ cần tìm (hoặc gõ 'exit' để thoát): ").strip()
        
        if tu_nhap_vao.lower() == 'exit':
            print("Đã thoát chương trình.")
            break
            
        if not tu_nhap_vao:
            continue
            
        danh_sach_van = tim_van(tu_nhap_vao)
        
        if danh_sach_van:
            print(f"\n=> Tổng cộng tìm thấy {len(danh_sach_van)} từ.")
        else:
            print("Không tìm thấy kết quả nào.")

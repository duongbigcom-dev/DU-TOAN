"""
Module chuẩn hóa chuỗi và bóc tách thông số kỹ thuật M&E.
Tuân thủ quy tắc: Chú thích giải thích TẠI SAO, biến và hàm đặt tên tiếng Anh rõ nghĩa.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Set, Any


def normalize_vietnamese_text(text: Optional[str]) -> str:
    """
    Chuẩn hóa văn bản tiếng Việt sang dạng Unicode chuẩn NFC và viết thường.
    
    TẠI SAO:
    Trong các file Excel do nhiều người soạn thảo, dấu tiếng Việt thường bị lẫn lộn
    giữa bảng mã Unicode tổ hợp (NFD) và Unicode dựng sẵn (NFC), ví dụ chữ 'òa' vs 'oà'.
    Nếu không đưa về NFC đồng nhất, phép so sánh chuỗi sẽ thất bại dù bề ngoài nhìn giống hệt nhau.
    """
    if not text:
        return ""
    text = str(text).strip()
    text = unicodedata.normalize("NFC", text)
    return text


def remove_vietnamese_accents(text: str) -> str:
    """
    Chuyển tiếng Việt có dấu thành không dấu để hỗ trợ tìm kiếm không phân biệt dấu.
    
    TẠI SAO:
    Người dùng khi nhập liệu thường gõ nhanh không dấu hoặc gõ sai quy tắc đặt dấu
    (ví dụ: 'thong so ky thuat' vs 'thông số kỹ thuật'). Chuyển về không dấu giúp
    so khớp từ khóa (keyword search) bao quát hơn.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    no_accent = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    no_accent = no_accent.replace("đ", "d").replace("Đ", "D")
    return no_accent


# ==============================================================================
# BỘ TỪ ĐIỂN 9 PHÂN HỆ VẬT TƯ M&E VÀ CÁC NHÓM TỪ ĐỒNG NGHĨA
# ==============================================================================
ME_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    # Phân hệ 1: Dây và cáp điện
    "PH_1_DAY_CAP": {
        "CABLE_BARE": ["cap dong tran", "dong tran", "cf", "cap tran"],
        "CABLE_CXV": ["cxv", "cap treo", "cu/xlpe/pvc", "cu/pvc/pvc"],
        "CABLE_BURIAL": ["cap ngam", "dsta", "data", "cu/xlpe/pvc/dsta", "cu/xlpe/dsta"],
        "CABLE_FIRE": ["cap chong chay", "chong chay", "fr", "frn", "mica", "cu.mica", "cu/mica", "fr-pvc", "frn-cxv"],
        "CABLE_VCSF": ["day don mem", "vcsf", "don mem", "day mem"],
        "CABLE_CV": ["day don cung", "cv", "don cung", "cu/pvc"],
        "CABLE_VCTFK": ["day o van", "vctfk", "o van", "day o van mem"],
        "CABLE_VCTF": ["day tron mem", "vctf", "tron mem"],
        "CABLE_DVV": ["day dieu khien", "dvv", "cap dieu khien"],
        "CABLE_SHIELD": ["chong nhieu", "dvv/sb", "dvv sb", "sb", "day chong nhieu"],
    },
    # Phân hệ 2: Ống luồn dây điện và phụ kiện
    "PH_2_ONG_LUON": {
        "CONDUIT_RIGID": ["ong luon", "ong luon day dien", "ong cung pvc", "ong luon pvc", "sp90", "ong cung"],
        "CONDUIT_FLEX": ["ong ruot ga", "ong mem", "ong dan hoi", "ruot ga", "ong luon dan hoi"],
        "CONDUIT_BOX": ["hop noi", "hop dau day", "gop noi", "hop chia", "hop noi trung gian", "box chia nga", "box chia", "hop chia nga", "hop chia nga thap"],
        "CONDUIT_BASE": ["de am", "de noi", "de don", "de doi", "de am chu nhat", "de am vuong", "de am nhua"],
        "ELEC_CABINET": ["tu dien", "tu chieu sang", "tu dong cat"],
    },
    # Phân hệ 3: Công tắc ổ cắm
    "PH_3_CTOC": {
        "SW_1G_1W": ["cong tac don 1 chieu", "cong tac 1 chieu 1 hat", "cong tac don", "1 hat 1 chieu", "cong tac 1 hat 1 chieu"],
        "SW_1G_2W": ["cong tac don 2 chieu", "cong tac don xoay chieu", "1 hat 2 chieu", "cong tac 1 hat 2 chieu"],
        "SW_2G_1W": ["cong tac doi 1 chieu", "cong tac 2 hat 1 chieu", "cong tac doi", "2 hat 1 chieu", "cong tac 2 hat 1 chieu"],
        "SW_2G_2W": ["cong tac doi 2 chieu", "cong tac doi xoay chieu", "2 hat 2 chieu", "cong tac 2 hat 2 chieu"],
        "SW_3G_1W": ["cong tac ba 1 chieu", "cong tac 3 hat 1 chieu", "cong tac ba", "3 hat 1 chieu", "cong tac 3 hat 1 chieu"],
        "SW_3G_2W": ["cong tac ba 2 chieu", "cong tac ba xoay chieu", "3 hat 2 chieu", "cong tac 3 hat 2 chieu"],
        "SW_4G_1W": ["cong tac bon 1 chieu", "cong tac 4 hat 1 chieu", "cong tac bon", "4 hat 1 chieu"],
        "SW_4G_2W": ["cong tac bon 2 chieu", "cong tac bon xoay chieu", "4 hat 2 chieu"],
        "SW_HEATER": ["cong tac 20a", "binh nong lanh", "cong tac 45a", "20a", "cong tac binh nong lanh", "cong tac 2 cuc 20a", "cong tac 2 cuc", "2 cuc 20a"],
        "SW_INTER": ["cong tac trung gian"],
        "SK_SINGLE": ["o cam don", "o cam 2 chau", "o cam 3 chau", "o cam don 3 chau", "2p+e", "kbn426uest"],
        "SK_DOUBLE": ["o cam doi", "o cam 2 chau doi", "o cam 3 chau doi", "o cam doi 3 chau", "kbnt426uest"],
        "SK_COVER": ["o cam doi co mat che", "co mat che", "mat che", "mat che chong nuoc", "co mat che chong nuoc", "chong nuoc", "e223r_tr"],
        "SK_NET_SINGLE": ["o cam mang don", "o cam data", "o cam rj45"],
        "SK_NET_DOUBLE": ["o cam mang doi", "o cam data doi"],
        "KEY_CARD": ["cong tac the tu", "the tu"],
        "DOOR_BELL_PANEL": ["khong lam phien", "xin don phong", "don phong", "wmf936", "bao don phong"],
        "DOOR_BELL": ["chuong cua", "chuong"],
    },
    # Phân hệ 4: Thang máng cáp
    "PH_4_THANG_MANG": {
        "LADDER": ["thang cap", "cable ladder"],
        "TRAY": ["mang cap", "cable tray", "trunking"],
        "TRAY_ELBOW": ["cut thang cap", "co thang cap", "cut mang cap", "co mang cap", "noi goc"],
        "TRAY_REDUCER": ["con thu thang cap", "noi giam thang cap", "con thu mang cap"],
        "TRAY_TEE": ["te thang cap", "te mang cap"],
        "TRAY_Z": ["z thang cap", "z mang cap"],
    },
    # Phân hệ 5: Thiết bị đóng cắt
    "PH_5_DONG_CAT": {
        "BREAKER_MCB": ["mcb", "aptomat te"],
        "BREAKER_MCCB": ["mccb", "aptomat khoi"],
        "BREAKER_RCBO": ["rcbo", "chong giat", "rccb", "elcb"],
        "BREAKER_ACB": ["acb", "may cat khong khi"],
        "CONTACTOR": ["contactor", "khoi dong tu"],
        "RELAY": ["relay", "ro le", "role", "ro le nhiet"],
    },
    # Phân hệ 6: Ống cấp thoát nước và phụ kiện
    "PH_6_CAP_THOAT_NUOC": {
        "PIPE_WATER": ["ong ppr", "ong upvc", "ong hdpe", "ong cap lanh", "ong cap nong", "ong nhua"],
        "PIPE_SOCKET": ["mang song", "socket", "dau noi", "noi thang", "noi tron", "mang xong"],
        "PIPE_REDUCER": ["con thu", "noi giam", "con giam", "giam", "con"],
        "PIPE_BUSHING": ["bac chuyen bac", "chuyen bac"],
        "PIPE_ELBOW_90": ["cut 90", "co 90", "cut 90 do", "co 90 do", "noi goc 90", "cut", "co"],
        "PIPE_ELBOW_45": ["chech", "cut 45", "co 45", "cut 135", "co 135", "noi goc 45", "loi", "chech 45", "chếch"],
        "PIPE_UNION": ["rac co", "union"],
        "PIPE_TEE_90": ["te", "tê", "ba chac 90", "tê deu", "te deu"],
        "PIPE_TEE_Y": ["chu y", "te 135", "te 45", "ba chac 45", "ba chac 135", "chu y 45"],
        "PIPE_CLEANOUT": ["bit xa", "thong tac", "bit xa thong tac", "clean out"],
        "PIPE_SIPHON": ["siphong", "xiphong", "xi phong", "si phong", "con tho", "meo", "xi phon"],
        "PIPE_CAP": ["nap bit", "bit chup", "bit tron", "nap chup", "bit dau", "nut bit", "bit"],
        "PIPE_VALVE_PLASTIC": ["van ppr", "van nhua", "van cong ppr", "van khoa ppr"],
        "PIPE_FLANGE": ["mat bich", "dau noi bich", "bich"],
        "PIPE_SLEEVE": ["dau noi thong san", "thong san"],
        "PIPE_INSPECT_TEE": ["te kiem tra"],
    },
    # Phân hệ 7: Van vòi và phụ kiện
    "PH_7_VAN_VOI": {
        "VALVE_GATE": ["van cong", "van cua", "van chan", "van hai chieu", "van 2 chieu", "gate valve", "van dong 2 chieu", "van cua dong"],
        "VALVE_CHECK": ["van 1 chieu", "van mot chieu", "check valve", "van kiem tra"],
        "VALVE_STRAINER": ["strainer", "y loc", "van y loc", "y-strainer", "bo loc rac"],
        "VALVE_FLEXIBLE": ["khop noi mem", "noi mem", "khop mem", "khop co gian", "cao su chong rung", "flexible joint"],
        "VALVE_FOOT": ["ro bom", "van chan", "ro hut", "luppe", "ruppe", "crepin", "foot valve"],
        "VALVE_FLOAT": ["van phao", "phao co", "phao thuy luc", "float valve"],
        "VALVE_BUTTERFLY": ["van buom", "butterfly valve"],
        "VALVE_BALL": ["van bi", "van bi dong", "van bi tay gat", "ball valve"],
        "VALVE_PRV": ["van giam ap", "pressure reducing valve", "prv"],
        "VALVE_AIR_VENT": ["van xa khi", "air vent"],
        "VALVE_WATER_HAMMER": ["van chong va"],
        "VALVE_BALANCING": ["van tuan hoan", "van hoi", "van can bang nhiet"],
        "DRAIN_ROOF": ["cau chan rac", "cau thoat mua", "qua cau chan rac"],
        "VENT_CAP": ["chup thong hoi"],
    },
    # Phân hệ 8: Ống đồng bảo ôn
    "PH_8_DONG_BAO_ON": {
        "COPPER_PIPE": ["ong dong", "copper pipe"],
        "INSULATION": ["bao on", "insulation", "superlon", "armacell"],
    },
    # Phân hệ 9: Ống gió và phụ kiện
    "PH_9_ONG_GIO": {
        "AIR_DUCT": ["ong gio"],
        "AIR_DUCT_ACC": ["phu kien ong gio"],
        "AIR_VALVE": ["van gio", "vcd", "fd"],
        "AIR_DIFFUSER": ["cua gio", "diffuser"],
    }
}


def get_me_category_tags(text: str) -> Set[str]:
    """
    Xác định tất cả các mã nhóm phân hệ tương ứng với văn bản.
    
    TẠI SAO:
    Phục vụ Tầng 2 trong Phễu tìm kiếm: Hãng -> Tên vật tư (đồng nghĩa) -> Kích thước -> Thông số.
    Nếu Form ghi 'Crepin' và Data ghi 'Rọ bơm', cả 2 đều trả về mã 'VALVE_FOOT',
    giúp hệ thống nhận diện đây là cùng một loại vật tư 100%.
    """
    if not text:
        return set()
    cleaned = remove_vietnamese_accents(text).lower()
    matched_tags = set()
    
    for ph_name, categories in ME_TAXONOMY.items():
        for tag, keywords in categories.items():
            for kw in keywords:
                # Kiểm tra từ khóa có mặt trong văn bản
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, cleaned):
                    matched_tags.add(tag)
                    break  # Đã khớp tag này thì chuyển tag tiếp theo
                    
    return matched_tags

# TẠI SAO:
# Form mời thầu thường viết tắt, gõ sai chính tả (ví dụ 'Schneder AV' thay vì 'Schneider',
# 'Cadisun' vs 'CADI-SUN'). Bản đồ này chuẩn hóa toàn bộ về một mã định danh duy nhất.
BRAND_SYNONYMS: Dict[str, str] = {
    "cadisun": "CADISUN",
    "cadi-sun": "CADISUN",
    "cadi sun": "CADISUN",
    "cáp điện cadisun": "CADISUN",
    "tien phong": "TIEN PHONG",
    "tiền phong": "TIEN PHONG",
    "nhựa tiền phong": "TIEN PHONG",
    "schneider": "SCHNEIDER",
    "schneder": "SCHNEIDER",
    "schneder av": "SCHNEIDER",
    "schneider electric": "SCHNEIDER",
    "ls": "LS",
    "ls electric": "LS",
    "ls industrial": "LS",
    "mitsubishi": "MITSUBISHI",
    "misubishi": "MITSUBISHI",
    "minh hoa": "MINH HOA",
    "minh hoà": "MINH HOA",
    "tozen": "TOZEN",
    "sino": "SINO",
    "sp": "SINO",
    "sp/ sino": "SINO",
    "sino/sp": "SINO",
    "sp/sino": "SINO",
    "liva": "LIVA",
    "panasonic": "PANASONIC",
    "panasonic/ tđ": "PANASONIC",
    "panasonic/td": "PANASONIC",
    "vesbo": "VESBO",
    "europipe": "EUROPIPE",
    "toan phat": "TOAN PHAT",
    "toàn phát": "TOAN PHAT",
    "superlon": "SUPERLON",
    "ruby": "RUBY",
    "commscope": "COMMSCOPE",
    "amp": "COMMSCOPE",
    "kangatang": "KANGATANG",
    "edenki": "EDENKI",
    "edenki electric": "EDENKI",
}


def normalize_brand_name(brand_raw: Optional[str]) -> str:
    """
    Nhận diện và chuẩn hóa tên hãng sản xuất.
    
    TẠI SAO:
    Đây là bộ lọc cốt lõi để thực hiện yêu cầu 'Bắt buộc chính xác Hãng sản xuất'.
    Hàm này sẽ bóc tách các tiền tố/hậu tố gây nhiễu để trích xuất ra Hãng chuẩn xác nhất.
    """
    if not brand_raw:
        return ""
    
    cleaned = normalize_vietnamese_text(brand_raw).lower()
    # Loại bỏ các ký tự đặc biệt không cần thiết
    cleaned = re.sub(r"[^\w\s\-\/\.]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # 1. Kiểm tra trực tiếp trong từ điển đồng nghĩa
    if cleaned in BRAND_SYNONYMS:
        return BRAND_SYNONYMS[cleaned]
    
    # 2. Kiểm tra nếu có chứa từ khóa của hãng
    for syn, canonical in BRAND_SYNONYMS.items():
        # Dùng regex biên giới từ để tránh nhầm (ví dụ 'ls' không bị nhầm trong 'pulse')
        pattern = r"\b" + re.escape(syn) + r"\b"
        if re.search(pattern, cleaned):
            return canonical
            
    # 3. Nếu chưa có trong danh sách chuẩn, chuyển về chữ in hoa không dấu chuẩn
    fallback = remove_vietnamese_accents(cleaned).upper()
    return fallback


def parse_cable_info(text: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Bóc tách toàn diện thông tin quy cách, số lõi, hệ số nhân và chủng loại của dây và cáp điện.
    
    Tuân thủ chặt chẽ các quy tắc chuyên sâu:
    1. Ký hiệu 2C, 3C, 4C, 5C tương đương số lõi (ví dụ 4C-10 -> 4x10, 1C-185 -> 1x185).
    2. Ký hiệu 2x1c nghĩa là 2 sợi 1 lõi (giá = 2x giá 1 lõi, ví dụ 2x1c1.5 = 2 sợi 1x1.5).
    3. Không xem xét đơn vị của tiết diện là mm2 hay mm (bỏ mm2, mm).
    4. Dây tiếp địa / Cáp tiếp địa: tiết diện nhỏ hơn 10 (< 10mm2: 0.5 - 6mm2) chọn VCSF; 
       tiết diện lớn hơn 6 (>= 10mm2) chọn CV (phân biệt với cáp đồng trần CF).
    5. Có FR, FRN thì phải chọn chống cháy FRN-CXV.
    6. Dây đơn 0.75, 1.0, 1.5, 2.5, 4, 6 nếu không ghi rõ điện áp thì ưu tiên chọn VCSF.
    7. Dây đôi 2x0.75, 2x1.0, 2x1.5, 2x2.5, 2x4 nếu không ghi rõ Tròn thì ưu tiên chọn Ô val VCTFK hơn VCTF.
    8. Nếu thông số kỹ thuật vượt quá quy cách NSX (Cu/PVC/PVC 0.6/1kV hoặc > 6mm2) -> chuyển sang CXV.
       CV 1x25 yêu cầu 450/750V -> chọn 0.6/1kV kèm ghi chú.
    """
    if not text:
        return None
        
    raw_text = str(text).strip()
    low = raw_text.lower()
    
    # Nếu là thiết bị điện hoặc phụ kiện (công tắc, ổ cắm, aptomat, tủ điện, ống luồn, đế âm, hộp chia), không phải dây cáp
    if any(k in low for k in ['cong tac', 'công tắc', 'o cam', 'ổ cắm', 'aptomat', 'mcb', 'mccb', 'tu dien', 'tủ điện', 'de am', 'đế âm', 'box chia', 'hop chia', 'hộp chia']):
        return None

    # Chuẩn hóa đơn vị: sqmm, mm2, mm² -> mm2
    text_clean = low.replace('sqmm', 'mm2').replace('mm²', 'mm2')
    # Bỏ đơn vị mm2 hoặc mm sau số
    text_clean = re.sub(r'(\d+(?:\.\d+)?)\s*(?:mm2|mm)\b', r'\1', text_clean)
    # 1. Chuẩn hóa dấu phẩy thập phân giữa các chữ số: 1,5 -> 1.5, 2,5 -> 2.5
    text_clean = re.sub(r'(\d+),(\d+)', r'\1.\2', text_clean)
    # 2. Chuẩn hóa dấu hoa thị nhân *: 4*35 -> 4x35, 1*70 -> 1x70, 4*2.5 -> 4x2.5
    text_clean = re.sub(r'(\d+)\s*[\*]\s*(\d+(?:\.\d+)?)', r'\1x\2', text_clean)
    
    multiplier = 1
    is_multi_single = False
    spec = None

    has_control_early = any(k in low for k in ['dieu khien', 'điều khiển', 'dvv'])
    has_shield_early = any(k in low for k in ['chong nhieu', 'chống nhiễu', 'dvv/sb', 'dvv sb']) or bool(re.search(r'\b(dvv\/sb|dvv[\s\-]sb|sb)\b', low))

    # 1. Phát hiện N x 1C (ví dụ: 2x1c1.5, 2x1cx1.5, 2x1c-1.5, 2*(1x1.5), 2x(1x1.5))
    m_multi_1c = re.search(r'(\d+)\s*[x\*]\s*1[c]\s*[-xX*]?\s*(\d+(?:\.\d+)?)', text_clean)
    if m_multi_1c:
        core_count = int(m_multi_1c.group(1))
        core_size = m_multi_1c.group(2)
        if core_size.endswith('.0'): core_size = core_size[:-2]

        if has_control_early or has_shield_early:
            # Cáp điều khiển / chống nhiễu không bao giờ có loại 1 lõi, 2x1C là cáp 2 lõi
            spec = f'{core_count}x{core_size}'
            multiplier = 1
            is_multi_single = False
        else:
            multiplier = core_count
            is_multi_single = True
            spec = f'1x{core_size}'
    else:
        # 2. nC phức tạp: 3cx25+1cx16
        m_comp_c = re.search(r'(\d+)[c]\s*[-x]?\s*(\d+(?:\.\d+)?)\s*[\+]\s*(\d+)[c]\s*[-x]?\s*(\d+(?:\.\d+)?)', text_clean)
        if m_comp_c:
            c1, s1, c2, s2 = m_comp_c.groups()
            if s1.endswith('.0'): s1 = s1[:-2]
            if s2.endswith('.0'): s2 = s2[:-2]
            spec = f'{c1}x{s1}+{c2}x{s2}'
        else:
            # Cặp phức tạp thường: 3x25+1x16
            m_comp = re.search(r'(\d+)[x]\s*(\d+(?:\.\d+)?)\s*[\+]\s*(\d+)[x]\s*(\d+(?:\.\d+)?)', text_clean)
            if m_comp:
                c1, s1, c2, s2 = m_comp.groups()
                if s1.endswith('.0'): s1 = s1[:-2]
                if s2.endswith('.0'): s2 = s2[:-2]
                spec = f'{c1}x{s1}+{c2}x{s2}'
            else:
                # Đơn/đa lõi với nC: 4C-10, 1C-185, 2Cx4, 1Cx2.5
                m_c = re.search(r'(\d+)[c]\s*[-x]?\s*(\d+(?:\.\d+)?)', text_clean)
                if m_c:
                    c, s = m_c.groups()
                    if s.endswith('.0'): s = s[:-2]
                    spec = f'{c}x{s}'
                else:
                    # Đa lõi chuẩn: 4x10, 3x2.5, 2x1.5
                    m_multi = re.search(r'(\d+)\s*[x]\s*(\d+(?:\.\d+)?)', text_clean)
                    if m_multi:
                        c, s = m_multi.groups()
                        if s.endswith('.0'): s = s[:-2]
                        spec = f'{c}x{s}'
                    else:
                        # 1 lõi đơn lẻ: 185, 70, 25, 2.5
                        m_single = re.search(r'(?:cu|cu\/pvc|cu\/xlpe|cv|fr|dây|cáp)?\s*(\d+(?:\.\d+)?)\b', text_clean)
                        if m_single:
                            s = m_single.group(1)
                            if s.endswith('.0'): s = s[:-2]
                            valid_sizes = {'0.5', '0.75', '1', '1.5', '2.5', '4', '6', '10', '16', '25', '35', '50', '70', '95', '120', '150', '185', '240', '300', '400', '500', '630', '800'}
                            if s in valid_sizes:
                                spec = f'1x{s}'

    if not spec:
        return None

    # Xác định đặc tính chủng loại cáp
    has_bare = any(k in low for k in ['dong tran', 'đồng trần', 'cap tran', 'cáp trần', 'cf', 'bare'])
    is_not_cable = any(k in low for k in ['o cam', 'ổ cắm', 'cong tac', 'công tắc', 'aptomat', 'mcb', 'mccb', 'tu dien', 'tủ điện'])
    has_earth = not is_not_cable and (
        any(k in low for k in ['tiep dia', 'tiếp địa', 'tiep dat', 'tiếp đất']) or 
        bool(re.search(r'\([eE]\)|\b[eE]\d+', raw_text))
    )
    has_fire = any(k in low for k in ['chong chay', 'chống cháy', 'fr', 'frn', 'cu.mica', 'cu/mica', 'fr-pvc'])
    has_burial = any(k in low for k in ['dsta', 'data', 'cap ngam', 'cáp ngầm', 'giap thep', 'giáp thép'])
    has_control = has_control_early
    has_shield = has_shield_early

    has_06_1kv = any(k in low for k in ['0.6/1kv', '0.6-1kv', '0,6/1kv', '0,6-1kv', '0.6/1', '1000v', '0.6kv'])
    has_450_750v = any(k in low for k in ['450/750v', '450/750', '750v', '300/500v', '300/500'])
    is_cv_explicit = bool(re.search(r'\bcv\b', low))
    is_vcsf_explicit = bool(re.search(r'\bvcsf\b', low))
    is_vctf_explicit = bool(re.search(r'\bvctf\b', low))
    is_vctfk_explicit = bool(re.search(r'\bvctfk\b', low))
    # Chú ý: Tránh bẫy chuỗi con 'vctf' nằm trong 'vctfk'
    is_round = any(k in low for k in ['tron', 'tròn', 'round']) or is_vctf_explicit
    has_xlpe = any(k in low for k in ['xlpe', 'cu/xlpe', 'cu/xlpe/pvc', 'cxv'])
    is_medium_voltage = any(k in low for k in ['trung the', 'trung thế', '24kv', '22kv', '35kv', 'medium voltage', 'mv cable'])

    target_family = None
    note_extra = []

    # 0. Cáp trung thế 24kV, 35kV (DATA BIGCOM chưa có cáp trung thế, không được tự ý lấy cáp hạ thế 0.6/1kV)
    if is_medium_voltage:
        target_family = 'MV_CABLE'
        note_extra.append('Cáp trung thế 24kV/35kV (chưa có trong Data Bigcom)')
    # 1. Cáp đồng trần CF (phân biệt với dây tiếp địa có bọc)
    elif has_bare:
        target_family = 'CF'
    # 2. Chống cháy -> FRN-CXV (Ưu tiên tuyệt đối: Có FR, FRN thì phải chọn chống cháy FRN-CXV)
    elif has_fire:
        target_family = 'FRN-CXV'
    # 3. Dây tiếp địa / Cáp tiếp địa (không có FR):
    # Quy tắc: Tiết diện nhỏ hơn 10 thì chọn VCSF (< 10mm2, tức 0.5 - 6mm2),
    #          Tiết diện lớn hơn 6 thì chọn CV (>= 10mm2, tức 10, 16, 25, 35, 50, 70, 95, 120, 240...)
    elif has_earth:
        m_sz = re.match(r'(\d+)x(\d+(?:\.\d+)?)', spec)
        core_val = float(m_sz.group(2)) if m_sz else 0.0
        if core_val == 0.0:
            m_single = re.search(r'(\d+(?:\.\d+)?)', spec)
            core_val = float(m_single.group(1)) if m_single else 0.0

        if 0 < core_val < 10.0:
            target_family = 'VCSF'
            note_extra.append(f'Dây tiếp địa {core_val}mm2 (<10mm2): chọn loại dây đơn mềm VCSF')
        else:
            target_family = 'CV'
            note_extra.append(f'Cáp tiếp địa {core_val}mm2 (>6mm2): chọn loại cáp đơn cứng CV')
    # 4. Cáp ngầm -> DSTA / DATA
    elif has_burial:
        target_family = 'DSTA'
    # 5. Dây chống nhiễu / điều khiển
    elif has_shield:
        target_family = 'DVV/SB'
    elif has_control:
        target_family = 'DVV'
    # 5.5 Ưu tiên tuyệt đối VCTFK khi hồ sơ ghi rõ VCTFK (dây ô-van mềm)
    elif is_vctfk_explicit:
        target_family = 'VCTFK'
    # 6. Cu/PVC/PVC hoặc Cu/PVC không có XLPE:
    elif 'cu/pvc/pvc' in low or ('cu/pvc' in low and not has_xlpe):
        m_sz = re.match(r'(\d+)x(\d+(?:\.\d+)?)', spec)
        core_count = int(m_sz.group(1)) if m_sz else 1
        core_val = float(m_sz.group(2)) if m_sz else 0.0

        if core_count == 1:
            if core_val <= 6.0:
                if has_06_1kv or is_cv_explicit or has_450_750v:
                    target_family = 'CV'
                    if has_450_750v:
                        note_extra.append('Chọn điện áp cao hơn 0.6/1kV (do quy cách NSX không có 450/750V)')
                else:
                    target_family = 'VCSF'
            else:
                target_family = 'CV'
                if has_450_750v:
                    note_extra.append('Chọn điện áp cao hơn 0.6/1kV (do quy cách NSX không có 450/750V)')
        elif core_count == 2:
            if has_06_1kv or core_val > 6.0:
                target_family = 'CXV'
                note_extra.append(f'Chuyển sang chủng loại CXV {spec} (do quy cách Cu/PVC/PVC chỉ có 300/500V <= 6mm2)')
            else:
                if (not is_round) or is_vctfk_explicit:
                    target_family = 'VCTFK'  # Ưu tiên Ô val
                else:
                    target_family = 'VCTF'
        else:
            # 3 lõi trở lên: Cu/PVC 3x1.5 là VCTF 3x1.5. Nếu vượt quy cách hoặc có 0.6/1kV mới sang CXV
            if has_06_1kv or core_val > 6.0 or core_count > 4:
                target_family = 'CXV'
                note_extra.append(f'Chuyển sang chủng loại CXV {spec} (do quy cách Cu/PVC/PVC chỉ có 300/500V <= 6mm2)')
            else:
                target_family = 'VCTF'
    # 6.5 Cáp có cách điện XLPE (Cu/XLPE/PVC hoặc CXV) -> BẮT BUỘC CHỌN CXV (kể cả 1 lõi hay đa lõi)
    elif has_xlpe:
        target_family = 'CXV'
    # 7. Dây đơn nhỏ (1x0.5 -> 1x6): nếu không yêu cầu rõ điện áp -> ưu tiên VCSF
    elif spec in {'1x0.5', '1x0.75', '1x1', '1x1.5', '1x2.5', '1x4', '1x6'}:
        if has_06_1kv or is_cv_explicit or has_450_750v:
            target_family = 'CV'
            if has_450_750v:
                note_extra.append('Chọn điện áp cao hơn 0.6/1kV (do quy cách NSX không có 450/750V)')
        elif is_vcsf_explicit:
            target_family = 'VCSF'
        else:
            target_family = 'VCSF'
    # 8. Dây đôi nhỏ (2x0.75 -> 2x4): nếu không ghi rõ tròn -> ưu tiên VCTFK
    elif spec in {'2x0.75', '2x1', '2x1.5', '2x2.5', '2x4'}:
        if has_06_1kv:
            target_family = 'CXV'
            note_extra.append(f'Chuyển sang chủng loại CXV {spec} do yêu cầu 0.6/1kV')
        elif is_round and not is_vctfk_explicit:
            target_family = 'VCTF'
        else:
            target_family = 'VCTFK'
    # 9. CV cỡ lớn (1x10 trở lên)
    elif is_cv_explicit or (spec.startswith('1x') and not has_xlpe):
        target_family = 'CV'
        if has_450_750v:
            note_extra.append('Chọn điện áp cao hơn 0.6/1kV (do quy cách NSX không có 450/750V)')
    elif spec.startswith('1x'):
        target_family = 'CXV'
    else:
        target_family = 'CXV'

    return {
        'spec': spec,
        'multiplier': multiplier,
        'is_multi_single': is_multi_single,
        'target_family': target_family,
        'note_extra': note_extra,
        'raw': raw_text
    }


def extract_cable_spec(text: str) -> Optional[str]:
    """
    Trích xuất tiết diện và số lõi của dây/cáp điện (ví dụ: '3x2.5+1x1.5', '3x2.5', '4x16', '185mm2').
    """
    info = parse_cable_info(text)
    return info['spec'] if info else None


def extract_pipe_size(text: str) -> Optional[str]:
    """
    Trích xuất kích thước danh định ống và phụ kiện (D20, D63, DN50, Ø63, 63x50...).
    
    TẠI SAO:
    Đường kính là thông số quyết định của ngành nước. Các kỹ sư thiết kế có thể viết 'D63', 'd63',
    'Ø63', 'DN50', 'd180/160' hay '63x50'. Hàm này sẽ chuẩn hóa về dạng đồng nhất để so sánh.
    """
    if not text:
        return None
    
    cleaned = text.lower().replace("ø", "d").replace("phi", "d").replace("dn", "d")
    
    # Dạng côn thu / tê thu: d63x50, d180/160, 63x50 (Chỉ nhận nếu cả 2 số đều là đường kính ống hợp lệ)
    pipe_sizes_set = {15, 16, 20, 25, 32, 40, 50, 60, 63, 65, 75, 80, 90, 100, 110, 125, 140, 150, 160, 180, 200, 225, 250, 315}
    reduction_pattern = r"(?:d)?(\d{2,3})[x\/](\d{2,3})"
    match_red = re.search(reduction_pattern, cleaned)
    if match_red:
        d1 = int(match_red.group(1))
        d2 = int(match_red.group(2))
        if d1 in pipe_sizes_set and d2 in pipe_sizes_set:
            return f"D{d1}x{d2}"
        
    # Dạng đường kính đơn: D63, D50, D20, D110
    match_d = re.search(r"(?:d|dn|phi|\b)(\d{2,3})\b", cleaned)
    if match_d:
        val = int(match_d.group(1))
        if val in pipe_sizes_set and str(val) not in {"90", "45", "135"}:
            return f"D{val}"
            
    return None


def extract_pressure_rating(text: str) -> Optional[str]:
    """
    Trích xuất cấp áp lực của ống và van (PN10, PN16, PN20, PN25, PN8...).
    
    TẠI SAO:
    Ống nước cùng kích thước D63 nhưng PN10 (dùng thoát/nước lạnh) có độ dày và giá thành
    rẻ hơn rất nhiều so với PN20 (ống chịu nhiệt nước nóng). Bắt buộc phải khớp đúng PN.
    """
    if not text:
        return None
    match = re.search(r"\bpn\s*(\d{1,2})\b", text.lower())
    if match:
        return f"PN{match.group(1)}"
    return None


def extract_breaker_spec(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Trích xuất thông số Aptomat / Thiết bị đóng cắt: Số cực (1P, 2P, 3P), Dòng định mức (16A, 100A), Dòng cắt (6kA).
    
    TẠI SAO:
    Aptomat trong tủ điện bắt buộc phải đúng 3 thông số này để đảm bảo an toàn điện và báo giá chính xác.
    """
    if not text:
        return None, None, None
        
    cleaned = text.upper()
    
    # 1. Số cực (Poles): 1P, 2P, 3P, 4P
    pole_match = re.search(r"\b([1-4])P\b", cleaned)
    pole = f"{pole_match.group(1)}P" if pole_match else None
    
    # 2. Dòng định mức (Current): 6A, 10A, 16A, 20A, 25A, 32A, 40A, 50A, 63A, 100A, 250A...
    amp_match = re.search(r"\b(\d{1,4})A\b", cleaned)
    amp = f"{amp_match.group(1)}A" if amp_match else None
    
    # 3. Dòng cắt ngắn mạch (Breaking capacity): 4.5kA, 6kA, 10kA, 18kA, 25kA...
    ka_match = re.search(r"\b(\d+(?:\.\d+)?)KA\b", cleaned)
    ka = f"{ka_match.group(1)}kA" if ka_match else None
    
    return pole, amp, ka

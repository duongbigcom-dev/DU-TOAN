"""
Module so khớp thông số vật tư và áp giá (M&E Matching Engine).
Tuân thủ tuyệt đối quy tắc: BẮT BUỘC CHÍNH XÁC HÃNG SẢN XUẤT.
Tuân thủ quy tắc: Chú thích giải thích TẠI SAO, biến và hàm đặt tên tiếng Anh rõ nghĩa.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from core.normalizer import (
    normalize_vietnamese_text,
    remove_vietnamese_accents,
    normalize_brand_name,
    parse_cable_info,
    extract_cable_spec,
    extract_pipe_size,
    extract_pressure_rating,
    extract_breaker_spec,
    get_me_category_tags,
)
from core.dynamic_loader import DataItem, DynamicDataLoader


class MatchResult:
    """
    Kết quả áp giá cho một dòng vật tư trong Form mời thầu.
    """
    def __init__(
        self,
        row_idx: int,
        req_stt: str,
        req_name: str,
        req_spec: str,
        req_code: str,
        req_brand: str,
        req_unit: str,
        req_qty: Any,
        status: str,  # 'exact' (xanh), 'near' (vàng), 'not_found' (đỏ)
        score: int,   # Điểm khớp từ 0 đến 100
        best_item: Optional[DataItem] = None,
        note: str = "",
        candidate_items: Optional[List[Dict[str, Any]]] = None,
        is_upsized: bool = False,
    ):
        self.row_idx = row_idx
        self.req_stt = req_stt
        self.req_name = req_name
        self.req_spec = req_spec
        self.req_code = req_code
        self.req_brand = req_brand
        self.req_unit = req_unit
        self.req_qty = req_qty
        self.status = status
        self.score = score
        self.best_item = best_item
        self.note = note
        self.candidate_items = candidate_items or []
        self.is_upsized = is_upsized

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành từ điển gửi về giao diện Web."""
        offer_data = {
            "name": self.best_item.name if self.best_item else "",
            "spec": self.best_item.spec if self.best_item else "",
            "code": self.best_item.code if self.best_item else "",
            "brand": self.best_item.brand_raw if self.best_item else "",
            "origin": self.best_item.origin if self.best_item else "",
            "price_mat": self.best_item.price_mat if self.best_item else 0.0,
            "price_lab": self.best_item.price_lab if self.best_item else 0.0,
        } if self.best_item else {
            "name": "", "spec": "", "code": "", "brand": "", "origin": "", "price_mat": 0.0, "price_lab": 0.0
        }

        return {
            "row_idx": self.row_idx,
            "req_stt": self.req_stt or f"Hàng {self.row_idx}",
            "req_name": self.req_name,
            "req_spec": self.req_spec,
            "req_code": self.req_code,
            "req_brand": self.req_brand,
            "req_unit": self.req_unit,
            "req_qty": self.req_qty,
            "status": self.status,
            "score": self.score,
            "offer": offer_data,
            "note": self.note,
            "candidates": self.candidate_items,
            "is_upsized": self.is_upsized,
        }


class MEMatcher:
    """
    Bộ máy so khớp chuyên dụng cho hệ Cơ Điện M&E.
    """
    def __init__(self, data_loader: DynamicDataLoader):
        self.loader = data_loader

    def match_item(
        self,
        row_idx: int,
        req_stt: str,
        req_name: str,
        req_spec: str,
        req_code: str,
        req_brand: str,
        req_unit: str,
        req_qty: Any,
    ) -> MatchResult:
        """
        Thực hiện so khớp một dòng vật tư theo quy tắc nghiêm ngặt: BẮT BUỘC ĐÚNG HÃNG.
        
        TẠI SAO:
        Trong đấu thầu M&E, nếu hồ sơ yêu cầu Cadisun mà áp giá LS hoặc Sino thì sai phạm
        nghiêm trọng. Do đó Hãng là điều kiện tiên quyết (Hard constraint), chỉ tìm kiếm
        trong phạm vi vật tư của đúng Hãng đó.
        """
        # Nếu dòng không có tên vật tư (ví dụ dòng trống hoặc dòng phân mục cha), bỏ qua
        if not req_name or len(req_name.strip()) == 0:
            return MatchResult(
                row_idx=row_idx,
                req_stt=req_stt,
                req_name=req_name,
                req_spec=req_spec,
                req_code=req_code,
                req_brand=req_brand,
                req_unit=req_unit,
                req_qty=req_qty,
                status="empty",
                score=0,
                note="Dòng trống",
            )

        # 1. BƯỚC 1: XÁC ĐỊNH VÀ CHUẨN HÓA HÃNG SẢN XUẤT
        normalized_req_brand = normalize_brand_name(req_brand)
        
        # Nếu cột Hãng trong Form bị trống, thử suy đoán từ chính tên vật tư
        if not normalized_req_brand:
            combined_req_text = f"{req_name} {req_spec} {req_code}".lower()
            for syn, canonical in {
                "cadisun": "CADISUN", "tiền phong": "TIEN PHONG", "tien phong": "TIEN PHONG",
                "schneider": "SCHNEIDER", "minh hòa": "MINH HOA", "minh hoà": "MINH HOA",
                "tozen": "TOZEN", "sino": "SINO", "liva": "LIVA", "vesbo": "VESBO",
                "europipe": "EUROPIPE", "toàn phát": "TOAN PHAT", "superlon": "SUPERLON"
            }.items():
                if syn in combined_req_text:
                    normalized_req_brand = canonical
                    break

        # Nếu vẫn không xác định được Hãng hoặc Hãng chưa có trong kho dữ liệu Bigcom
        if not normalized_req_brand or normalized_req_brand not in self.loader.items_by_brand:
            return MatchResult(
                row_idx=row_idx,
                req_stt=req_stt,
                req_name=req_name,
                req_spec=req_spec,
                req_code=req_code,
                req_brand=req_brand,
                req_unit=req_unit,
                req_qty=req_qty,
                status="not_found",
                score=0,
                best_item=None,
                note="Không tìm thấy dữ liệu",
            )

        # 2. BƯỚC 2: KHOANH VÙNG DANH SÁCH ỨNG VIÊN CỦA ĐÚNG HÃNG ĐÓ
        # TẠI SAO: Đảm bảo 100% không bao giờ lấy nhầm vật tư của hãng khác.
        brand_candidates: List[DataItem] = self.loader.items_by_brand[normalized_req_brand]
        if not brand_candidates:
            return MatchResult(
                row_idx=row_idx,
                req_stt=req_stt,
                req_name=req_name,
                req_spec=req_spec,
                req_code=req_code,
                req_brand=req_brand,
                req_unit=req_unit,
                req_qty=req_qty,
                status="not_found",
                score=0,
                best_item=None,
                note="Không tìm thấy dữ liệu",
            )

        # ==============================================================================
        # PHỄU SO KHỚP 4 TẦNG: HÃNG -> TÊN VẬT TƯ -> KÍCH THƯỚC -> THÔNG SỐ KỸ THUẬT
        # ==============================================================================
        
        # Bóc tách thông số từ hồ sơ mời thầu
        full_req_str = f"{req_name} {req_spec} {req_code}"
        req_tags = get_me_category_tags(full_req_str)
        req_cable_info = parse_cable_info(full_req_str)
        req_cable_spec = req_cable_info['spec'] if req_cable_info else extract_cable_spec(full_req_str)
        req_pipe_size = extract_pipe_size(full_req_str)
        req_pressure = extract_pressure_rating(full_req_str)
        req_pole, req_amp, req_ka = extract_breaker_spec(full_req_str)
        
        req_clean_search = remove_vietnamese_accents(full_req_str.lower())
        req_tokens = set(re.findall(r"\w+", req_clean_search))

        scored_candidates: List[Tuple[int, int, DataItem, str]] = []

        for cand in brand_candidates:
            score = 0
            reason = []
            cand_clean = cand.search_text
            cand_tags = cand.category_tags

            # --------------------------------------------------------------------------
            # TẦNG 2: KHỚP TÊN VẬT TƯ (CATEGORY VIA 9 PHÂN HỆ TỪ ĐỒNG NGHĨA & HỆ DÂY CÁP)
            # --------------------------------------------------------------------------
            category_matched = False
            
            # XỬ LÝ ĐẶC THÙ CHO PHÂN HỆ 1: HỆ DÂY VÀ CÁP ĐIỆN
            if req_cable_info and normalized_req_brand == "CADISUN":
                tf = req_cable_info['target_family']
                c_code = cand.code or ""
                c_name_low = cand.name.lower()
                
                family_matched = False
                if tf == 'CF' and (c_code.startswith('CF') or 'đồng trần' in c_name_low):
                    family_matched = True
                elif tf == 'CV' and c_code.startswith('CV '):
                    family_matched = True
                elif tf == 'FRN-CXV' and (c_code.startswith('FRN-CXV') or 'frn' in c_code.lower()):
                    family_matched = True
                elif tf == 'VCTFK' and c_code.startswith('VCTFK'):
                    family_matched = True
                elif tf == 'VCTF' and c_code.startswith('VCTF ') and not c_code.startswith('VCTFK'):
                    family_matched = True
                elif tf == 'VCSF' and c_code.startswith('VCSF'):
                    family_matched = True
                elif tf == 'CXV' and c_code.startswith('CXV ') and not c_code.startswith('FRN-CXV'):
                    family_matched = True
                elif tf == 'DSTA' and (c_code.startswith('DSTA') or c_code.startswith('DATA')):
                    family_matched = True
                elif tf == 'DVV/SB' and (c_code.startswith('DVV/SB') or 'sb' in c_code.lower()):
                    family_matched = True
                elif tf == 'DVV' and c_code.startswith('DVV ') and not 'sb' in c_code.lower():
                    family_matched = True
                
                if family_matched:
                    score += 50
                    category_matched = True
                    reason.append(f"Khớp chủng loại {tf}")
                else:
                    # Khác chủng loại cáp yêu cầu theo 8 quy tắc -> bỏ qua ứng viên này
                    continue
            elif req_tags:
                shared_tags = req_tags.intersection(cand_tags)
                if shared_tags:
                    matched_tag = list(shared_tags)[0]
                    if matched_tag.startswith(('SW_', 'SK_')):
                        score += 65
                    elif matched_tag.startswith(('CONDUIT_', 'BREAKER_')):
                        score += 60
                    else:
                        score += 45
                    category_matched = True
                    reason.append(f"Khớp phân hệ {matched_tag}")
                else:
                    # Kiểm tra loại trừ nếu rơi vào các nhóm xung đột
                    if "VALVE_CHECK" in req_tags and "VALVE_GATE" in cand_tags:
                        continue
                    if "VALVE_GATE" in req_tags and "VALVE_CHECK" in cand_tags:
                        continue
                    if "VALVE_FOOT" in req_tags and ("VALVE_GATE" in cand_tags or "VALVE_CHECK" in cand_tags):
                        continue
                    if "PIPE_ELBOW_90" in req_tags and ("PIPE_TEE_90" in cand_tags or "PIPE_REDUCER" in cand_tags):
                        continue
                    if "PIPE_TEE_90" in req_tags and ("PIPE_ELBOW_90" in cand_tags or "PIPE_SOCKET" in cand_tags):
                        continue
                    if "CABLE_BURIAL" in req_tags and "CABLE_CXV" in cand_tags:
                        continue
                    if "CABLE_FIRE" in req_tags and "CABLE_BARE" in cand_tags:
                        continue
            else:
                common_type_words = ["ong", "cut", "te", "con", "mang song", "bich", "van", "cap", "day"]
                for w in common_type_words:
                    if w in req_tokens and w in cand_clean:
                        score += 20
                        category_matched = True
                        reason.append(f"Khớp từ khóa {w}")
                        break

            # --------------------------------------------------------------------------
            # TẦNG 3: KHỚP KÍCH THƯỚC ĐỊNH LƯỢNG (DIMENSIONS / SIZES)
            # --------------------------------------------------------------------------
            dimension_matched = False

            # 3.1 Dây / Cáp điện: Tiết diện (Số lõi x Tiết diện)
            if req_cable_spec:
                cand_cable = cand.cable_spec or extract_cable_spec(cand_clean)
                is_cf = (req_cable_info and req_cable_info['target_family'] == 'CF') or 'cf' in cand.code.lower()
                
                if is_cf:
                    pure_sz = req_cable_spec.replace('1x', '')
                    if cand.code == f'CF {pure_sz}' or f' {pure_sz}mm2' in cand_clean:
                        score += 40
                        dimension_matched = True
                        reason.append(f"Khớp tiết diện {pure_sz}")
                    else:
                        continue
                elif cand_cable == req_cable_spec:
                    score += 40
                    dimension_matched = True
                    reason.append(f"Khớp tiết diện {req_cable_spec}")
                elif cand_cable:
                    continue  # Khác tiết diện cáp thì loại bỏ ngay
            # 3.2 Ống nước & Van: Đường kính danh định D / DN
            elif req_pipe_size:
                cand_pipe = cand.pipe_size or extract_pipe_size(cand_clean)
                if cand_pipe == req_pipe_size:
                    score += 40
                    dimension_matched = True
                    reason.append(f"Khớp kích thước {req_pipe_size}")
                elif cand_pipe:
                    # Chấp nhận kích thước chuyển đổi gần nhất (VD: D63 ~ DN50 / DN65)
                    if req_pipe_size in ["D63", "D50", "D65"] and cand_pipe in ["D50", "D63", "D65"]:
                        score += 25
                        dimension_matched = True
                        reason.append(f"Gần kích thước {req_pipe_size} ~ {cand_pipe}")
                    else:
                        continue  # Sai đường kính thì loại bỏ
            # 3.3 Aptomat & Công tắc ổ cắm: Số cực và dòng định mức
            elif req_pole or req_amp:
                if req_pole and cand.pole and req_pole == cand.pole:
                    score += 20
                    reason.append(f"Khớp số cực {req_pole}")
                amp_num = req_amp.replace('A', '') if req_amp else ''
                if req_amp and (cand.amp == req_amp or (amp_num and amp_num in cand.code)):
                    score += 25
                    dimension_matched = True
                    reason.append(f"Khớp dòng định mức {req_amp}")

            # --------------------------------------------------------------------------
            # TẦNG 4: KHỚP THÔNG SỐ KỸ THUẬT (SPECIFICATIONS / ATTRIBUTES)
            # --------------------------------------------------------------------------
            # 4.1 Cấp áp lực ống/van (PN)
            if req_pressure:
                cand_pressure = cand.pressure or extract_pressure_rating(cand_clean)
                if cand_pressure and cand_pressure == req_pressure:
                    score += 15
                    reason.append(f"Khớp áp lực {req_pressure}")
                elif cand_pressure:
                    score -= 10

            # 4.2 Cấp chống cháy / chậm cháy
            is_req_fire = "CABLE_FIRE" in req_tags or any(k in req_clean_search for k in ["chong chay", "fr", "mica", "cu.mica", "cu/mica"])
            is_cand_fire = "CABLE_FIRE" in cand_tags or any(k in cand_clean for k in ["chong chay", "fr", "mica"])
            if is_req_fire and is_cand_fire:
                score += 15
                reason.append("Khớp tiêu chuẩn chống cháy")
            elif is_req_fire and not is_cand_fire:
                score -= 25  # Yêu cầu chống cháy mà chào cáp thường là sai lệch lớn

            # 4.3 Vật liệu ống (PPR, HDPE, uPVC)
            for mat in ["ppr", "hdpe", "upvc", "pvc"]:
                if mat in req_clean_search:
                    if mat in cand_clean:
                        score += 15
                        reason.append(f"Khớp vật liệu {mat.upper()}")
                    else:
                        score -= 15
                    break

            # 4.4 Dòng cắt Aptomat (kA)
            if req_ka and cand.ka and req_ka == cand.ka:
                score += 10
                reason.append(f"Khớp dòng cắt {req_ka}")

            # 4.5 Trùng tên vật tư chính xác (ví dụ: 'Đế âm' vs 'Đế âm')
            clean_cand_name = remove_vietnamese_accents(cand.name.lower()).strip()
            clean_req_name = remove_vietnamese_accents(req_name.lower()).strip()
            if clean_cand_name == clean_req_name:
                score += 30
                reason.append("Trùng khớp tên vật tư")

            # Điểm tương đồng văn bản phụ trợ
            cand_tokens = set(re.findall(r"\w+", cand_clean))
            common_tokens = req_tokens.intersection(cand_tokens)
            if common_tokens:
                score += min(10, len(common_tokens) * 2)

            if score > 0:
                is_exact_dim = 1 if (
                    (req_cable_spec and cand.cable_spec == req_cable_spec) or
                    (req_pipe_size and cand.pipe_size == req_pipe_size) or
                    (req_amp and cand.amp == req_amp)
                ) else 0
                scored_candidates.append((score, is_exact_dim, cand, " | ".join(reason)))

        # Sắp xếp ứng viên: Ưu tiên khớp chính xác kích thước định lượng trước, sau đó theo điểm số
        scored_candidates.sort(key=lambda x: (x[1], x[0], -x[2].item_id), reverse=True)

        # 5. BƯỚC 5: ĐÁNH GIÁ KẾT QUẢ VÀ CHỌN PHƯƠNG ÁN TỐT NHẤT
        is_upsized = False
        # Nếu chưa tìm thấy ứng viên khớp chính xác tiết diện, áp dụng quy tắc người dùng:
        # "Nếu đã tìm đúng hãng, chủng loại, thông số nhưng không có tiết diện yêu cầu thì chọn tiết diện lớn hơn gần nhất (Có bôi đỏ ghi chú)"
        if (not scored_candidates or scored_candidates[0][0] < 50) and req_cable_info and normalized_req_brand == "CADISUN":
            tf = req_cable_info['target_family']
            m_req_sz = re.match(r'^(\d+)x(\d+(?:\.\d+)?)$', req_cable_spec) if req_cable_spec else None
            if m_req_sz and tf not in ('MV_CABLE', None):
                req_cores = int(m_req_sz.group(1))
                req_size = float(m_req_sz.group(2))
                
                best_up_cand = None
                min_up_size = 999999.0
                
                for cand in brand_candidates:
                    c_code = cand.code or ""
                    c_name_low = cand.name.lower()
                    
                    family_matched = False
                    if tf == 'CF' and (c_code.startswith('CF') or 'đồng trần' in c_name_low): family_matched = True
                    elif tf == 'CV' and c_code.startswith('CV '): family_matched = True
                    elif tf == 'FRN-CXV' and (c_code.startswith('FRN-CXV') or 'frn' in c_code.lower()): family_matched = True
                    elif tf == 'VCTFK' and c_code.startswith('VCTFK'): family_matched = True
                    elif tf == 'VCTF' and c_code.startswith('VCTF ') and not c_code.startswith('VCTFK'): family_matched = True
                    elif tf == 'VCSF' and c_code.startswith('VCSF'): family_matched = True
                    elif tf == 'CXV' and c_code.startswith('CXV ') and not c_code.startswith('FRN-CXV'): family_matched = True
                    elif tf == 'DSTA' and (c_code.startswith('DSTA') or c_code.startswith('DATA')): family_matched = True
                    elif tf == 'DVV/SB' and (c_code.startswith('DVV/SB') or 'sb' in c_code.lower()): family_matched = True
                    elif tf == 'DVV' and c_code.startswith('DVV ') and not 'sb' in c_code.lower(): family_matched = True
                    
                    if not family_matched:
                        continue
                        
                    c_spec = cand.cable_spec or extract_cable_spec(f"{cand.name} {cand.code} {cand.spec}")
                    if not c_spec and tf == 'CF':
                        m_cf = re.match(r'^CF\s*(\d+(?:\.\d+)?)$', c_code)
                        if m_cf: c_spec = f"1x{m_cf.group(1)}"
                    
                    if not c_spec:
                        continue
                        
                    m_c = re.match(r'^(\d+)x(\d+(?:\.\d+)?)$', c_spec)
                    if not m_c:
                        continue
                        
                    cand_cores = int(m_c.group(1))
                    cand_size = float(m_c.group(2))
                    
                    if cand_cores == req_cores and cand_size > req_size:
                        if cand_size < min_up_size:
                            min_up_size = cand_size
                            best_up_cand = cand
                            
                if best_up_cand:
                    is_upsized = True
                    cand_display_spec = best_up_cand.cable_spec or extract_cable_spec(f"{best_up_cand.name} {best_up_cand.code} {best_up_cand.spec}") or f"{req_cores}x{min_up_size:g}"
                    scored_candidates = [(95, 1, best_up_cand, f"Chọn tiết diện lớn hơn gần nhất: {cand_display_spec} (Yêu cầu {req_cable_spec})")]

        if not scored_candidates or scored_candidates[0][0] < 50:
            return MatchResult(
                row_idx=row_idx,
                req_stt=req_stt,
                req_name=req_name,
                req_spec=req_spec,
                req_code=req_code,
                req_brand=req_brand,
                req_unit=req_unit,
                req_qty=req_qty,
                status="not_found",
                score=0,
                best_item=None,
                note="Không tìm thấy dữ liệu",
                is_upsized=False,
            )

        best_raw_score, _, best_cand, best_reason = scored_candidates[0]
        best_score = min(100, best_raw_score)
        
        # Xử lý hệ số nhân (nếu là dạng N x 1C như 2x1c1.5 = 2 sợi 1x1.5)
        import copy
        final_cand = copy.copy(best_cand)
        note_prefixes = []

        if req_cable_info:
            mult = req_cable_info.get('multiplier', 1)
            if mult > 1:
                final_cand.price_mat = best_cand.price_mat * mult
                final_cand.price_lab = best_cand.price_lab * mult
                note_prefixes.append(f"Gồm {mult} sợi 1 lõi {req_cable_spec} (Đơn giá = {mult} x {best_cand.price_mat:,.0f} đ)")
            
            if req_cable_info.get('note_extra'):
                note_prefixes.extend(req_cable_info['note_extra'])

        # Đóng gói danh sách top 5 ứng viên để gửi về Web UI phục vụ chức năng 'Đổi mã chào thầu'
        top_candidates = []
        for s, _, c, r in scored_candidates[:5]:
            cand_p_mat = c.price_mat * (req_cable_info['multiplier'] if req_cable_info and req_cable_info.get('multiplier', 1) > 1 else 1)
            cand_p_lab = c.price_lab * (req_cable_info['multiplier'] if req_cable_info and req_cable_info.get('multiplier', 1) > 1 else 1)
            top_candidates.append({
                "item_id": c.item_id,
                "score": min(100, s),
                "name": c.name,
                "code": c.code,
                "spec": c.spec,
                "origin": c.origin,
                "price_mat": cand_p_mat,
                "price_lab": cand_p_lab,
                "reason": r,
            })

        # Phân loại trạng thái màu:
        # Xanh lá (exact): Khớp cao >= 85%
        # Vàng (near): Khớp gần nhất 50% - 84%
        status = "exact" if best_score >= 85 else "near"
        
        note_parts = []
        if note_prefixes:
            note_parts.extend(note_prefixes)
        if is_upsized:
            note_parts.append(best_reason)
        elif best_reason:
            note_parts.append(f"Khớp {best_score}% ({best_reason})")
        else:
            note_parts.append(f"Khớp {best_score}%")
            
        note_str = " | ".join(note_parts)

        return MatchResult(
            row_idx=row_idx,
            req_stt=req_stt,
            req_name=req_name,
            req_spec=req_spec,
            req_code=req_code,
            req_brand=req_brand,
            req_unit=req_unit,
            req_qty=req_qty,
            status=status,
            score=best_score,
            best_item=final_cand,
            note=note_str,
            candidate_items=top_candidates,
            is_upsized=is_upsized,
        )

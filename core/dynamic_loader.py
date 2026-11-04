"""
Module đọc dữ liệu động (Dynamic Data Loader) từ file Excel.
Tự động quét toàn bộ Sheet, tự động phát hiện cột tiêu đề, không gán cứng số dòng hay tên sheet.
Tuân thủ quy tắc: Chú thích giải thích TẠI SAO, biến và hàm đặt tên tiếng Anh rõ nghĩa.
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple
import openpyxl
from core.normalizer import (
    normalize_vietnamese_text,
    remove_vietnamese_accents,
    normalize_brand_name,
    extract_cable_spec,
    extract_pipe_size,
    extract_pressure_rating,
    extract_breaker_spec,
    get_me_category_tags,
)


class DataItem:
    """
    Lớp đại diện cho một bản ghi vật tư trong kho dữ liệu giá.
    """
    def __init__(
        self,
        item_id: int,
        sheet_name: str,
        row_idx: int,
        name: str,
        code: str,
        spec: str,
        brand: str,
        brand_raw: str,
        origin: str,
        unit: str,
        price_mat: float,
        price_lab: float,
    ):
        self.item_id = item_id
        self.sheet_name = sheet_name
        self.row_idx = row_idx
        self.name = name.strip()
        self.code = code.strip()
        self.spec = spec.strip()
        self.brand = brand  # Tên Hãng đã chuẩn hóa (VD: 'CADISUN', 'TIEN PHONG')
        self.brand_raw = brand_raw  # Tên Hãng gốc trong file
        self.origin = origin.strip() or "Việt Nam"
        self.unit = unit.strip()
        self.price_mat = price_mat  # Giá chưa VAT sau chiết khấu
        self.price_lab = price_lab  # Đơn giá nhân công
        
        # Bóc tách trước các thông số định lượng để tăng tốc độ so khớp sau này
        full_spec_text = f"{self.name} {self.code} {self.spec}"
        self.cable_spec = extract_cable_spec(full_spec_text)
        self.pipe_size = extract_pipe_size(full_spec_text)
        self.pressure = extract_pressure_rating(full_spec_text)
        self.pole, self.amp, self.ka = extract_breaker_spec(full_spec_text)
        
        # Chuỗi tìm kiếm tổng hợp không dấu phục vụ so khớp nhanh
        self.search_text = remove_vietnamese_accents(full_spec_text.lower())
        
        # Tiền xử lý phân hệ từ đồng nghĩa một lần duy nhất khi nạp vào RAM
        self.category_tags = get_me_category_tags(full_spec_text)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành từ điển để gửi về giao diện Web API."""
        return {
            "item_id": self.item_id,
            "sheet_name": self.sheet_name,
            "row_idx": self.row_idx,
            "name": self.name,
            "code": self.code,
            "spec": self.spec,
            "brand": self.brand,
            "brand_raw": self.brand_raw,
            "origin": self.origin,
            "unit": self.unit,
            "price_mat": self.price_mat,
            "price_lab": self.price_lab,
            "cable_spec": self.cable_spec,
            "pipe_size": self.pipe_size,
            "pressure": self.pressure,
            "category_tags": list(self.category_tags),
        }


class DynamicDataLoader:
    """
    Bộ nạp dữ liệu động quét toàn bộ các sheet và tự động xác định cấu trúc cột.
    """
    def __init__(self):
        self.all_items: List[DataItem] = []
        self.items_by_brand: Dict[str, List[DataItem]] = {}
        self.sheet_summaries: List[Dict[str, Any]] = []
        self.total_items: int = 0
        self.loaded_file_path: Optional[str] = None

    def load_data_file(self, file_path: str) -> bool:
        """
        Nạp file Excel DATA BIGCOM.
        
        TẠI SAO:
        Hàm này đọc từng sheet một cách độc lập, tự tìm dòng tiêu đề và suy đoán cột.
        Nhờ đó người dùng có thể tự do thêm sheet mới, đổi tên sheet hay thêm dòng mà
        phần mềm không bao giờ bị gãy vỡ (robust & resilient).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        self.all_items.clear()
        self.items_by_brand.clear()
        self.sheet_summaries.clear()
        self.loaded_file_path = file_path

        # Đọc chế độ data_only=True để lấy giá trị tính toán thay vì công thức Excel
        workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=False)
        item_counter = 0

        for sheet in workbook.worksheets:
            sheet_name = sheet.title.strip()
            # 1. Tự động phát hiện vị trí các cột trong sheet
            col_map, header_row = self._detect_columns(sheet)
            
            # Nếu sheet không có cột Tên hoặc Đơn giá (sheet trống/ghi chú), bỏ qua
            if not col_map.get("name") or (not col_map.get("price_mat") and not col_map.get("price_list")):
                self.sheet_summaries.append({
                    "sheet_name": sheet_name,
                    "row_count": 0,
                    "status": "Trống hoặc không có cấu trúc giá"
                })
                continue

            sheet_item_count = 0
            # 2. Duyệt từ dòng kế tiếp sau dòng tiêu đề
            for row_idx in range(header_row + 1, sheet.max_row + 1):
                name_val = self._get_cell_value(sheet, row_idx, col_map.get("name"))
                if not name_val:
                    continue  # Bỏ qua dòng trống tên vật tư

                code_val = self._get_cell_value(sheet, row_idx, col_map.get("code")) or ""
                spec_val = self._get_cell_value(sheet, row_idx, col_map.get("spec")) or ""
                alt_name_val = self._get_cell_value(sheet, row_idx, col_map.get("alt_name")) or ""
                if alt_name_val:
                    spec_val = f"{spec_val} ({alt_name_val})".strip()
                brand_val = self._get_cell_value(sheet, row_idx, col_map.get("brand")) or ""
                origin_val = self._get_cell_value(sheet, row_idx, col_map.get("origin")) or "Việt Nam"
                unit_val = self._get_cell_value(sheet, row_idx, col_map.get("unit")) or ""

                # Xác định Hãng: Nếu cột Hãng trong dòng để trống, lấy theo tên Sheet (VD: Sheet 'Tiền Phong', 'Vesbo')
                normalized_brand = normalize_brand_name(brand_val)
                if not normalized_brand:
                    normalized_brand = normalize_brand_name(sheet_name)

                # Xác định đơn giá Vật tư (Ưu tiên giá sau chiết khấu)
                price_mat = self._parse_number(self._get_cell_value(sheet, row_idx, col_map.get("price_mat")))
                price_lab = self._parse_number(self._get_cell_value(sheet, row_idx, col_map.get("price_lab")))
                
                # Nếu chưa có giá vật tư mà có giá bìa + chiết khấu thì tính tự động
                if price_mat == 0.0 and col_map.get("price_list"):
                    price_list = self._parse_number(self._get_cell_value(sheet, row_idx, col_map.get("price_list")))
                    discount = self._parse_number(self._get_cell_value(sheet, row_idx, col_map.get("discount")))
                    if price_list > 0:
                        price_mat = price_list * (1.0 - discount) if 0 < discount < 1 else price_list

                item_counter += 1
                sheet_item_count += 1
                item = DataItem(
                    item_id=item_counter,
                    sheet_name=sheet_name,
                    row_idx=row_idx,
                    name=name_val,
                    code=code_val,
                    spec=spec_val,
                    brand=normalized_brand,
                    brand_raw=brand_val or sheet_name,
                    origin=origin_val,
                    unit=unit_val,
                    price_mat=price_mat,
                    price_lab=price_lab,
                )
                self.all_items.append(item)
                
                # Thêm vào chỉ mục theo Hãng
                if normalized_brand not in self.items_by_brand:
                    self.items_by_brand[normalized_brand] = []
                self.items_by_brand[normalized_brand].append(item)

            self.sheet_summaries.append({
                "sheet_name": sheet_name,
                "row_count": sheet_item_count,
                "status": f"Đã nạp {sheet_item_count} vật tư"
            })

        self.total_items = len(self.all_items)
        workbook.close()
        return True

    def _detect_columns(self, sheet) -> Tuple[Dict[str, int], int]:
        """
        Dò tìm dòng tiêu đề và bản đồ cột trong 5 dòng đầu tiên của sheet.
        
        TẠI SAO:
        Trong bảng tính kỹ thuật M&E, tiêu đề thường là dạng 'Merged Cells' hoặc trải dài
        trên 2-3 dòng (ví dụ dòng 2 ghi 'Tên VT', 'Đơn giá', dòng 3 ghi 'Vật liệu', 'Vật tư', 'Nhân công').
        Phương pháp tối ưu là tổng hợp (aggregate) toàn bộ nhãn văn bản của từng cột qua các dòng 1..4
        để không bao giờ bị mất cột 'Tên' hay nhầm 'Vật liệu' sang cột giá.
        """
        col_map: Dict[str, int] = {}
        max_header_row = 1
        
        # 1. Thu thập nhãn tổng hợp của từng cột từ dòng 1 đến dòng 5
        col_labels: Dict[int, List[str]] = {}
        for r in range(1, min(6, (sheet.max_row or 1) + 1)):
            for c in range(1, min((sheet.max_column or 1) + 1, 30)):
                cell_val = str(sheet.cell(row=r, column=c).value or "").strip().lower()
                if cell_val:
                    if c not in col_labels:
                        col_labels[c] = []
                    col_labels[c].append(cell_val)
                    if r > max_header_row and any(k in remove_vietnamese_accents(cell_val) for k in [
                        "ten", "ma", "don gia", "vat tu", "nhan cong", "dvt", "hang", "xuat xu"
                    ]):
                        max_header_row = r

        # 2. Phân tích ngữ nghĩa cho từng cột dựa trên tổng hợp các dòng tiêu đề
        for c, labels in col_labels.items():
            combined_raw = " ".join(labels)
            combined = remove_vietnamese_accents(combined_raw)

            # Cột Tên gọi khác (Lưu ý: kiểm tra trước để tránh nhầm với Tên gọi chính)
            if "ten goi khac" in combined or "ten khac" in combined:
                col_map["alt_name"] = c
            # Cột Tên vật tư chính
            elif any(k in combined for k in ["ten goi", "ten vt", "ten vat tu", "ten hang", "dien giai", "description"]):
                col_map["name"] = c
            # Cột Mã hiệu
            elif any(k in combined for k in ["ma vt", "ma hieu", "model", "ma hang", "part number"]):
                if "code" not in col_map:
                    col_map["code"] = c
            # Cột Đơn giá Vật tư (Lưu ý: phân biệt 'vat lieu' là tên vật liệu ống vs 'vat tu' là đơn giá)
            elif any(k in combined for k in ["don gia chua vat", "don gia vat tu", "chua vat"]) or ("don gia" in combined and "nhan cong" not in combined and "vat lieu" not in combined):
                if "price_mat" not in col_map:
                    col_map["price_mat"] = c
            elif "vat tu" in combined and "price_mat" not in col_map:
                col_map["price_mat"] = c
            # Cột Đơn giá Nhân công
            elif any(k in combined for k in ["nhan cong", "nc", "labor"]):
                if "price_lab" not in col_map:
                    col_map["price_lab"] = c
            # Cột Hãng sản xuất
            elif any(k in combined for k in ["hang/ nhan hieu", "nhan hieu", "nsx", "nha san xuat", "brand"]):
                if "brand" not in col_map:
                    col_map["brand"] = c
            elif "hang" in combined and "gia hang" not in combined and "price_list" not in col_map:
                # Nếu chỉ có chữ 'hang' mà đứng sau cột giá thì thường là giá niêm yết của Hãng
                if c >= 10:
                    col_map["price_list"] = c
                elif "brand" not in col_map:
                    col_map["brand"] = c
            # Cột Xuất xứ
            elif any(k in combined for k in ["xuat xu", "xuat su", "origin"]):
                if "origin" not in col_map:
                    col_map["origin"] = c
            # Cột Đơn vị tính
            elif any(k in combined for k in ["don vi tinh", "dvt", "don vi", "unit"]):
                if "unit" not in col_map:
                    col_map["unit"] = c
            # Cột Chiết khấu
            elif any(k in combined for k in ["chiet khau", "ck", "discount"]):
                if "discount" not in col_map:
                    col_map["discount"] = c
            # Cột Giá bìa / Giá niêm yết của Hãng
            elif any(k in combined for k in ["gia bia", "bia", "niem yet", "gia hang"]):
                if "price_list" not in col_map:
                    col_map["price_list"] = c
            # Cột Thông số kỹ thuật
            elif any(k in combined for k in ["thong so", "quy cach", "kich thuoc", "cau truc", "spec"]):
                if "spec" not in col_map:
                    col_map["spec"] = c

        # Trường hợp phụ: nếu chưa tìm thấy cột Tên, kiểm tra cột 1 hoặc 2
        if "name" not in col_map:
            for c in [2, 1, 3]:
                if c in col_labels:
                    col_map["name"] = c
                    break

        return col_map, max_header_row

    def _get_cell_value(self, sheet, row: int, col: Optional[int]) -> Optional[str]:
        """Lấy giá trị chuỗi an toàn từ một ô tính."""
        if not col:
            return None
        val = sheet.cell(row=row, column=col).value
        return str(val).strip() if val is not None else None

    def _parse_number(self, val_raw: Any) -> float:
        """Chuyển đổi chuỗi tiền tệ thành số thực (float)."""
        if val_raw is None:
            return 0.0
        if isinstance(val_raw, (int, float)):
            return float(val_raw)
        try:
            # Loại bỏ dấu phẩy ngăn cách hàng nghìn hoặc ký tự tiền tệ
            cleaned = re.sub(r"[^\d\.]", "", str(val_raw).replace(",", ""))
            return float(cleaned) if cleaned else 0.0
        except Exception:
            return 0.0

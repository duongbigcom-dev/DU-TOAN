"""
Module xuất file Excel Báo Giá đã áp giá.
Đảm bảo: Kẻ bảng sắc nét, định dạng số tiền tệ chuẩn chỉ, tô màu trực quan (Xanh / Vàng / Đỏ).
Tuân thủ quy tắc: Chú thích giải thích TẠI SAO, biến và hàm đặt tên tiếng Anh rõ nghĩa.
"""

import os
from typing import Dict, List, Any
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from core.matcher import MatchResult


class ExcelExporter:
    """
    Bộ xuất file Excel chuyên nghiệp giữ trọn vẹn định dạng gốc và bổ sung định dạng chuẩn chỉ.
    """
    def __init__(self):
        # 1. Định nghĩa các màu tô (Pastel fills) chuẩn chuyên nghiệp, dịu mắt
        # TẠI SAO: Trong hồ sơ dự toán, màu chói gắt sẽ gây nhức mắt khi xem hàng nghìn dòng.
        # Sử dụng tone màu pastel dịu nhẹ theo chuẩn quốc tế:
        self.fill_green = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")  # Xanh lá nhạt
        self.fill_yellow = PatternFill(start_color="FFF9C4", end_color="FFF9C4", fill_type="solid") # Vàng nhạt
        self.fill_red = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")    # Đỏ nhạt
        
        # 2. Định nghĩa kiểu đường viền (Border) mỏng sắc nét
        # TẠI SAO: Đáp ứng yêu cầu 'Kẻ bảng chuẩn chỉ', tất cả các ô trong bảng dự toán
        # đều phải có viền kẻ liền mạch theo chuẩn hồ sơ mời thầu.
        thin_side = Side(border_style="thin", color="B0BEC5")
        self.cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # 3. Định nghĩa Font chữ chuẩn Arial / Times New Roman
        self.font_data = Font(name="Arial", size=10)
        self.font_price = Font(name="Arial", size=10, bold=True)
        self.font_note = Font(name="Arial", size=9, italic=True)
        self.font_note_upsized = Font(name="Arial", size=9, bold=True, color="DC2626")

        # 4. Định nghĩa căn lề (Alignment)
        self.align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
        self.align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.align_right = Alignment(horizontal="right", vertical="center")

    def export_quoted_form(
        self,
        template_form_path: str,
        match_results: List[MatchResult],
        output_file_path: str,
    ) -> str:
        """
        Ghi dữ liệu đã áp giá vào đúng các cột I -> P của file FORM BÁO GIÁ.
        
        TẠI SAO:
        Mở trực tiếp file mẫu gốc bằng openpyxl để giữ nguyên toàn bộ các dòng tiêu đề,
        logo công ty, các cột yêu cầu A->H và công thức tính tổng thành tiền ở các cột sau.
        """
        if not os.path.exists(template_form_path):
            raise FileNotFoundError(f"Không tìm thấy file mẫu: {template_form_path}")

        workbook = openpyxl.load_workbook(template_form_path)
        sheet = workbook.active

        # Tạo từ điển tra cứu nhanh theo row_idx
        result_map: Dict[int, MatchResult] = {res.row_idx: res for res in match_results}

        # Duyệt qua các dòng và điền kết quả chào thầu
        for row_idx, res in result_map.items():
            if res.status == "empty":
                continue

            # Các cột thông số chào thầu cần điền:
            # I: Tên vật tư chào thầu
            # J: Quy cách / Thông số chào thầu
            # K: Model / Mã hiệu
            # L: Hãng / Nhãn hiệu
            # M: Xuất xứ
            # N: Đơn giá Vật liệu
            # O: Đơn giá Nhân công
            # P: Ghi chú

            # Xác định trạng thái có tìm thấy vật tư hay không
            is_found = bool(res.best_item and res.status != "not_found")

            # Xác định màu highlight theo trạng thái khớp
            current_fill = self.fill_green if (is_found and res.status == "exact") else (
                self.fill_yellow if (is_found and res.status == "near") else self.fill_red
            )

            # 1. Cột I: Tên vật tư chào thầu (nếu không tìm thấy thì để trống)
            cell_i = sheet.cell(row=row_idx, column=9)
            cell_i.value = res.best_item.name if is_found else None
            cell_i.font = self.font_data
            cell_i.alignment = self.align_left
            cell_i.border = self.cell_border
            cell_i.fill = current_fill

            # 2. Cột J: Quy cách / Thông số chào thầu (nếu không tìm thấy thì để trống)
            cell_j = sheet.cell(row=row_idx, column=10)
            cell_j.value = res.best_item.spec if is_found else None
            cell_j.font = self.font_data
            cell_j.alignment = self.align_left
            cell_j.border = self.cell_border
            cell_j.fill = current_fill

            # 3. Cột K: Model / Mã hiệu (nếu không tìm thấy thì để trống)
            cell_k = sheet.cell(row=row_idx, column=11)
            cell_k.value = res.best_item.code if is_found else None
            cell_k.font = self.font_data
            cell_k.alignment = self.align_center
            cell_k.border = self.cell_border
            cell_k.fill = current_fill

            # 4. Cột L: Hãng / Nhãn hiệu (nếu không tìm thấy thì để trống)
            cell_l = sheet.cell(row=row_idx, column=12)
            cell_l.value = res.best_item.brand_raw if is_found else None
            cell_l.font = self.font_data
            cell_l.alignment = self.align_center
            cell_l.border = self.cell_border
            cell_l.fill = current_fill

            # 5. Cột M: Xuất xứ (nếu không tìm thấy thì để trống)
            cell_m = sheet.cell(row=row_idx, column=13)
            cell_m.value = res.best_item.origin if is_found else None
            cell_m.font = self.font_data
            cell_m.alignment = self.align_center
            cell_m.border = self.cell_border
            cell_m.fill = current_fill

            # 6. Cột N: Đơn giá Vật liệu (Giá chưa VAT sau chiết khấu)
            cell_n = sheet.cell(row=row_idx, column=14)
            if is_found and res.best_item.price_mat > 0:
                cell_n.value = round(res.best_item.price_mat)
                cell_n.number_format = "#,##0"
            else:
                cell_n.value = None
            cell_n.font = self.font_price
            cell_n.alignment = self.align_right
            cell_n.border = self.cell_border
            cell_n.fill = current_fill

            # 7. Cột O: Đơn giá Nhân công
            cell_o = sheet.cell(row=row_idx, column=15)
            if is_found and res.best_item.price_lab > 0:
                cell_o.value = round(res.best_item.price_lab)
                cell_o.number_format = "#,##0"
            else:
                cell_o.value = None
            cell_o.font = self.font_data
            cell_o.alignment = self.align_right
            cell_o.border = self.cell_border
            cell_o.fill = current_fill

            # 8. Cột P: Ghi chú (nếu không tìm thấy thì ghi: 'Không tìm thấy dữ liệu', nếu upsize thì bôi đỏ)
            cell_p = sheet.cell(row=row_idx, column=16)
            cell_p.value = res.note if is_found else "Không tìm thấy dữ liệu"
            if is_found and getattr(res, "is_upsized", False):
                cell_p.font = self.font_note_upsized
            else:
                cell_p.font = self.font_note
            cell_p.alignment = self.align_left
            cell_p.border = self.cell_border
            cell_p.fill = current_fill

            # Đảm bảo các ô bên vế A->H cũng được kẻ viền bảng sắc nét
            for c in range(1, 9):
                req_cell = sheet.cell(row=row_idx, column=c)
                req_cell.border = self.cell_border

        # Đảm bảo thư mục lưu file tồn tại
        os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
        workbook.save(output_file_path)
        workbook.close()
        return output_file_path


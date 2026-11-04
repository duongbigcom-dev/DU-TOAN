"""
Ứng dụng Web Dự Toán Cơ Điện M&E - Smart Matching Pro.
Tự động nhận diện quy cách, ghép nối đa sheet và lập bảng giá chào thầu chuyên nghiệp.
Tuân thủ quy tắc: Chú thích giải thích TẠI SAO, biến và hàm đặt tên tiếng Anh rõ nghĩa.
"""

import os
import sys

# Dam bao stdout/stderr dung ma hoa UTF-8 tren Windows console
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

import json
import traceback
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, send_file
import openpyxl

# Thiết lập đường dẫn thư mục gốc dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.dynamic_loader import DynamicDataLoader, DataItem
from core.matcher import MEMatcher, MatchResult
from core.excel_exporter import ExcelExporter

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "me_estimator_smart_matching_pro_secret_key"

# Khởi tạo các đối tượng xử lý toàn cục
data_loader = DynamicDataLoader()
matcher: Optional[MEMatcher] = None
excel_exporter = ExcelExporter()

# Lưu trữ trạng thái trong bộ nhớ RAM
current_match_results: List[MatchResult] = []
current_form_items: List[Dict[str, Any]] = []
data_file_path = os.path.join(BASE_DIR, "DATA BIGCOM.xlsx")
form_file_path = os.path.join(BASE_DIR, "FORM BÁO GIÁ.xlsx")


def get_default_file_status() -> Dict[str, Any]:
    """Kiểm tra sự hiện diện của 2 file mặc định trong thư mục."""
    has_data = os.path.exists(data_file_path)
    has_form = os.path.exists(form_file_path)
    return {
        "has_data": has_data,
        "has_form": has_form,
        "data_filename": "DATA BIGCOM.xlsx" if has_data else None,
        "form_filename": "FORM BÁO GIÁ.xlsx" if has_form else None,
        "data_loaded": data_loader.total_items > 0,
        "total_data_items": data_loader.total_items,
        "total_sheets": len(data_loader.sheet_summaries),
        "total_form_rows": len(current_form_items),
        "total_matched": len(current_match_results),
    }


@app.route("/")
def index():
    """Giao diện chính của bảng điều khiển áp giá."""
    status = get_default_file_status()
    return render_template("index.html", status=status)


@app.route("/api/status", methods=["GET"])
def api_status():
    """Trả về trạng thái hiện tại của dữ liệu."""
    return jsonify(get_default_file_status())


@app.route("/api/load_all_default", methods=["POST"])
def api_load_all_default():
    """
    Nạp nhanh 2 file có sẵn trong thư mục (DATA BIGCOM.xlsx và FORM BÁO GIÁ.xlsx).
    
    TẠI SAO:
    Phục vụ nút 'Nạp Nhanh Dữ Liệu Có Sẵn' trên giao diện như trong ảnh mẫu của người dùng,
    giúp chuyên viên dự toán không mất công kéo thả từng file nếu file đã nằm sẵn trong folder.
    """
    global matcher, current_form_items
    try:
        if not os.path.exists(data_file_path):
            return jsonify({"success": False, "error": "Không tìm thấy file DATA BIGCOM.xlsx trong thư mục!"})
        if not os.path.exists(form_file_path):
            return jsonify({"success": False, "error": "Không tìm thấy file FORM BÁO GIÁ.xlsx trong thư mục!"})

        # 1. Nạp file DATA BIGCOM
        data_loader.load_data_file(data_file_path)
        matcher = MEMatcher(data_loader)

        # 2. Nạp file FORM BÁO GIÁ
        current_form_items = read_form_file(form_file_path)

        return jsonify({
            "success": True,
            "data_total_items": data_loader.total_items,
            "data_total_sheets": len(data_loader.sheet_summaries),
            "form_total_rows": len(current_form_items),
            "sheet_summaries": data_loader.sheet_summaries,
            "message": f"Đã nạp thành công {data_loader.total_items} vật tư từ DATA và {len(current_form_items)} dòng từ FORM!"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/auto_match", methods=["POST"])
def api_auto_match():
    """
    Thực hiện áp giá tự động toàn bộ các dòng của Form báo giá.
    
    TẠI SAO:
    Đây là luồng xử lý chính kết hợp đồng hồ cát (loading animation) trên giao diện.
    Hàm này duyệt qua toàn bộ các dòng, bóc tách thông số và so khớp nghiêm ngặt theo Hãng.
    """
    global current_match_results, matcher, current_form_items
    try:
        if not matcher or data_loader.total_items == 0:
            if os.path.exists(data_file_path):
                data_loader.load_data_file(data_file_path)
                matcher = MEMatcher(data_loader)
            else:
                return jsonify({"success": False, "error": "Chưa nạp cơ sở dữ liệu DATA BIGCOM!"})

        if not current_form_items:
            if os.path.exists(form_file_path):
                current_form_items = read_form_file(form_file_path)
            else:
                return jsonify({"success": False, "error": "Chưa có dữ liệu FORM BÁO GIÁ!"})

        current_match_results.clear()
        exact_count = 0
        near_count = 0
        not_found_count = 0

        # Tiến hành so khớp từng dòng
        for row in current_form_items:
            res = matcher.match_item(
                row_idx=row["row_idx"],
                req_stt=row["req_stt"],
                req_name=row["req_name"],
                req_spec=row["req_spec"],
                req_code=row["req_code"],
                req_brand=row["req_brand"],
                req_unit=row["req_unit"],
                req_qty=row["req_qty"],
            )
            current_match_results.append(res)
            
            if res.status == "exact":
                exact_count += 1
            elif res.status == "near":
                near_count += 1
            elif res.status == "not_found":
                not_found_count += 1

        # Chuyển đổi thành danh sách dict để gửi về Web
        items_payload = [res.to_dict() for res in current_match_results if res.status != "empty"]

        return jsonify({
            "success": True,
            "total_items": len(items_payload),
            "exact_count": exact_count,
            "near_count": near_count,
            "not_found_count": not_found_count,
            "items": items_payload,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/change_candidate", methods=["POST"])
def api_change_candidate():
    """
    Cho phép kỹ sư đổi mã chào thầu cho một dòng cụ thể khi bấm nút 'Đổi mã chào thầu'.
    """
    try:
        data = request.json or {}
        row_idx = int(data.get("row_idx"))
        item_id = int(data.get("item_id"))

        # Tìm vật tư mới từ kho dữ liệu
        new_item = next((item for item in data_loader.all_items if item.item_id == item_id), None)
        if not new_item:
            return jsonify({"success": False, "error": "Không tìm thấy vật tư được chọn!"})

        # Cập nhật kết quả áp giá của dòng tương ứng
        for res in current_match_results:
            if res.row_idx == row_idx:
                res.best_item = new_item
                res.status = "exact"
                res.score = 100
                res.note = f"Đã chọn thủ công: {new_item.code or new_item.name}"
                return jsonify({"success": True, "updated_item": res.to_dict()})

        return jsonify({"success": False, "error": f"Không tìm thấy dòng {row_idx}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/export_excel", methods=["GET"])
def api_export_excel():
    """
    Xuất file Excel hoàn chỉnh có kẻ bảng, tô màu chuẩn chỉ và tải về máy.
    """
    try:
        if not current_match_results:
            return "Chưa có dữ liệu đã áp giá để xuất file! Vui lòng bấm 'Áp Giá Tự Động' trước.", 400

        output_dir = os.path.join(BASE_DIR, "exports")
        output_file = os.path.join(output_dir, "FORM_BAO_GIA_DA_AP_GIA.xlsx")

        excel_exporter.export_quoted_form(
            template_form_path=form_file_path,
            match_results=current_match_results,
            output_file_path=output_file,
        )

        return send_file(
            output_file,
            as_attachment=True,
            download_name="FORM_BAO_GIA_DA_AP_GIA.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        traceback.print_exc()
        return f"Lỗi khi xuất file Excel: {str(e)}", 500


def read_form_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Đọc toàn bộ các dòng yêu cầu từ file FORM BÁO GIÁ.
    
    TẠI SAO:
    File Form có các dòng tiêu đề từ 1 đến 4. Dữ liệu vật tư bắt đầu từ dòng 5.
    Hàm này lấy chính xác các cột yêu cầu A->G và số dòng thực tế trong Excel.
    """
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    rows_data = []

    for r in range(5, sheet.max_row + 1):
        name_val = str(sheet.cell(row=r, column=2).value or "").strip()
        # Bỏ qua dòng nếu hoàn toàn không có tên vật tư
        if not name_val:
            continue

        stt_val = str(sheet.cell(row=r, column=1).value or "").strip()
        spec_val = str(sheet.cell(row=r, column=3).value or "").strip()
        code_val = str(sheet.cell(row=r, column=4).value or "").strip()
        brand_val = str(sheet.cell(row=r, column=5).value or "").strip()
        unit_val = str(sheet.cell(row=r, column=6).value or "").strip()
        qty_val = sheet.cell(row=r, column=7).value

        rows_data.append({
            "row_idx": r,
            "req_stt": stt_val or f"Hàng {r}",
            "req_name": name_val,
            "req_spec": spec_val,
            "req_code": code_val,
            "req_brand": brand_val,
            "req_unit": unit_val,
            "req_qty": qty_val,
        })

    workbook.close()
    return rows_data


if __name__ == "__main__":
    # Khởi động server nội bộ cổng 5000
    print("=" * 60)
    print("DỰ TOÁN CƠ ĐIỆN M&E - SMART MATCHING PRO (WEB APPLICATION)")
    print("Khởi chạy tại: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)

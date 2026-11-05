"""
Ứng dụng Web Dự Toán Cơ Điện M&E - Smart Matching Pro.
Tự động nhận diện quy cách, ghép nối đa sheet và lập bảng giá chào thầu chuyên nghiệp.
Tuân thủ quy tắc: Chú thích giải thích TẠI SAO, biến và hàm đặt tên tiếng Anh rõ nghĩa.
"""

import os
import sys

# Đảm bảo mã hóa UTF-8 trên Windows console để không bị lỗi UnicodeEncodeError khi in tiếng Việt
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import json
import socket
import threading
import time
import traceback
import webbrowser
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, send_file
import openpyxl

# Thiết lập đường dẫn thư mục gốc dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.dynamic_loader import DynamicDataLoader, DataItem
from core.matcher import MEMatcher, MatchResult
from core.match_memory import MatchMemory
from core.excel_exporter import ExcelExporter

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "me_estimator_smart_matching_pro_secret_key"
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # Cho phép tải file Excel tới 100MB

# Khởi tạo các đối tượng xử lý toàn cục
data_loader = DynamicDataLoader()
match_memory = MatchMemory()
matcher: Optional[MEMatcher] = None
excel_exporter = ExcelExporter()

# Lưu trữ trạng thái trong bộ nhớ RAM
current_match_results: List[MatchResult] = []
current_form_items: List[Dict[str, Any]] = []


def get_data_file_path() -> Optional[str]:
    """Tìm đường dẫn file DATA BIGCOM có sẵn trong thư mục làm việc."""
    candidates = [
        "DATA BIGCOM.xlsx",
        "DATA_BIGCOM.xlsx",
        "DATA BIGCOM .xlsx",
    ]
    for c in candidates:
        p = os.path.join(BASE_DIR, c)
        if os.path.exists(p):
            return p
    for fname in os.listdir(BASE_DIR):
        if fname.upper().startswith("DATA") and fname.endswith(".xlsx"):
            return os.path.join(BASE_DIR, fname)
    return None


def get_form_file_path() -> Optional[str]:
    """Tìm đường dẫn file FORM BÁO GIÁ có sẵn trong thư mục làm việc."""
    candidates = [
        "FORM BÁO GIÁ.xlsx",
        "FORM BAO GIA.xlsx",
        "FORM_BAO_GIA.xlsx",
        "FORM BÁO GIÁ .xlsx",
        "FORM BAO GIA .xlsx",
    ]
    for c in candidates:
        p = os.path.join(BASE_DIR, c)
        if os.path.exists(p):
            return p
    for fname in os.listdir(BASE_DIR):
        if fname.upper().startswith("FORM") and fname.endswith(".xlsx") and "DA_AP_GIA" not in fname.upper():
            return os.path.join(BASE_DIR, fname)
    return None


def get_default_file_status() -> Dict[str, Any]:
    """Kiểm tra sự hiện diện của 2 file mặc định trong thư mục."""
    df_path = get_data_file_path()
    ff_path = get_form_file_path()
    has_data = df_path is not None
    has_form = ff_path is not None
    return {
        "has_data": has_data,
        "has_form": has_form,
        "data_filename": os.path.basename(df_path) if has_data else None,
        "form_filename": os.path.basename(ff_path) if has_form else None,
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


@app.route("/standalone")
@app.route("/bc_smp")
def standalone():
    """Phục vụ phiên bản HTML độc lập chạy trực tiếp trên trình duyệt."""
    bc_path = os.path.join(BASE_DIR, "BC_SMP.html")
    if os.path.exists(bc_path):
        return send_file(bc_path)
    return "File BC_SMP.html không tồn tại!", 404


@app.route("/api/status", methods=["GET"])
def api_status():
    """Trả về trạng thái hiện tại của dữ liệu."""
    return jsonify(get_default_file_status())


@app.route("/api/load_all_default", methods=["POST"])
def api_load_all_default():
    """
    Nạp nhanh 2 file có sẵn trong thư mục (DATA BIGCOM và FORM BÁO GIÁ).
    
    TẠI SAO:
    Phục vụ nút 'Nạp Nhanh Dữ Liệu Có Sẵn' trên giao diện như trong ảnh mẫu của người dùng,
    giúp chuyên viên dự toán không mất công kéo thả từng file nếu file đã nằm sẵn trong folder.
    """
    global matcher, current_form_items
    try:
        data_path = get_data_file_path()
        form_path = get_form_file_path()

        if not data_path:
            return jsonify({"success": False, "error": "Không tìm thấy file DATA BIGCOM.xlsx trong thư mục!"})
        if not form_path:
            return jsonify({"success": False, "error": "Không tìm thấy file FORM BÁO GIÁ.xlsx trong thư mục!"})

        # 1. Nạp file DATA BIGCOM
        data_loader.load_data_file(data_path)
        matcher = MEMatcher(data_loader, match_memory=match_memory)

        # 2. Nạp file FORM BÁO GIÁ
        current_form_items = read_form_file(form_path)

        return jsonify({
            "success": True,
            "data_filename": os.path.basename(data_path),
            "form_filename": os.path.basename(form_path),
            "data_total_items": data_loader.total_items,
            "data_total_sheets": len(data_loader.sheet_summaries),
            "form_total_rows": len(current_form_items),
            "sheet_summaries": data_loader.sheet_summaries,
            "message": f"Đã nạp thành công {data_loader.total_items} vật tư từ DATA và {len(current_form_items)} dòng từ FORM!"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/upload_data", methods=["POST"])
def api_upload_data():
    """Cho phép tải lên hoặc kéo thả trực tiếp file DATA Excel vào Web App."""
    global matcher
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "Không tìm thấy file được gửi lên!"})
        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"success": False, "error": "Tên file không hợp lệ!"})

        save_path = os.path.join(BASE_DIR, "DATA BIGCOM.xlsx")
        file.save(save_path)

        data_loader.load_data_file(save_path)
        matcher = MEMatcher(data_loader, match_memory=match_memory)

        return jsonify({
            "success": True,
            "filename": file.filename,
            "data_total_items": data_loader.total_items,
            "data_total_sheets": len(data_loader.sheet_summaries),
            "sheet_summaries": data_loader.sheet_summaries,
            "message": f"Đã nạp thành công {data_loader.total_items} vật tư từ {len(data_loader.sheet_summaries)} sheet!"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/upload_form", methods=["POST"])
def api_upload_form():
    """Cho phép tải lên hoặc kéo thả trực tiếp file FORM Excel vào Web App."""
    global current_form_items
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "Không tìm thấy file được gửi lên!"})
        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"success": False, "error": "Tên file không hợp lệ!"})

        save_path = os.path.join(BASE_DIR, "FORM BÁO GIÁ.xlsx")
        file.save(save_path)

        current_form_items = read_form_file(save_path)

        return jsonify({
            "success": True,
            "filename": file.filename,
            "form_total_rows": len(current_form_items),
            "message": f"Đã đọc thành công {len(current_form_items)} dòng mời thầu!"
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
        data_path = get_data_file_path()
        form_path = get_form_file_path()

        if not matcher or data_loader.total_items == 0:
            if data_path:
                data_loader.load_data_file(data_path)
                matcher = MEMatcher(data_loader, match_memory=match_memory)
            else:
                return jsonify({"success": False, "error": "Chưa nạp cơ sở dữ liệu DATA BIGCOM!"})

        if not current_form_items:
            if form_path:
                current_form_items = read_form_file(form_path)
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

        # Cập nhật kết quả áp giá của dòng tương ứng và ghi nhớ vào MatchMemory
        for res in current_match_results:
            if res.row_idx == row_idx:
                res.best_item = new_item
                res.status = "exact"
                res.score = 100
                res.note = f"Đã chọn thủ công: {new_item.code or new_item.name}"
                
                # Lưu vào bộ nhớ học máy
                match_memory.record_match(
                    req_name=res.req_name,
                    req_spec=res.req_spec,
                    req_brand=res.req_brand,
                    item_id=new_item.item_id,
                    item_code=new_item.code,
                    item_name=new_item.name,
                    item_spec=new_item.spec,
                    item_brand=new_item.brand_raw,
                )
                return jsonify({
                    "success": True,
                    "updated_item": res.to_dict(),
                    "total_memory_records": match_memory.total_records
                })

        return jsonify({"success": False, "error": f"Không tìm thấy dòng {row_idx}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/export_excel", methods=["GET", "POST"])
def api_export_excel():
    """
    Xuất file Excel hoàn chỉnh có kẻ bảng, tô màu chuẩn chỉ và tải về máy.
    """
    try:
        if not current_match_results:
            return "Chưa có dữ liệu đã áp giá để xuất file! Vui lòng bấm 'Áp Giá Tự Động' trước.", 400

        form_path = get_form_file_path()
        if not form_path:
            return "Không tìm thấy file mẫu FORM BÁO GIÁ.xlsx để xuất kết quả!", 404

        output_dir = os.path.join(BASE_DIR, "exports")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "FORM_BAO_GIA_DA_AP_GIA.xlsx")

        excel_exporter.export_quoted_form(
            template_form_path=form_path,
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


@app.route("/api/memory", methods=["GET"])
def api_get_memory():
    """Lấy danh sách các cặp vật tư đã được học và ghi nhớ."""
    return jsonify({
        "success": True,
        "total_records": match_memory.total_records,
        "memories": match_memory.memories,
    })


@app.route("/api/memory/clear", methods=["POST"])
def api_clear_memory():
    """Xóa toàn bộ bộ nhớ học máy khi cần thiết lập lại."""
    match_memory.memories = {}
    match_memory.save()
    return jsonify({"success": True, "total_records": 0})


def find_available_port(start_port: int = 5000, max_tries: int = 20) -> int:
    """Tự động kiểm tra và chọn cổng khả dụng (5000, 5001, 5050...) tránh lỗi cổng bận."""
    for p in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex(('127.0.0.1', p)) != 0:
                    return p
        except Exception:
            return p
    return start_port


def open_browser(port: int):
    """Mở trình duyệt tự động sau khi server Flask đã sẵn sàng."""
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    port = find_available_port(5000)
    print("=" * 60)
    print("DỰ TOÁN CƠ ĐIỆN M&E - BIGCOM SMART MATCHING PRO (WEB APPLICATION)")
    print(f"Khởi chạy tại địa chỉ: http://127.0.0.1:{port}")
    print("Trình duyệt web sẽ tự động mở trong giây lát...")
    print("=" * 60)

    # Chạy luồng tự động mở trình duyệt sau khi máy chủ bắt đầu
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False)

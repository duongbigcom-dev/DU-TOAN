"""
Module quản lý bộ nhớ học máy từ thao tác ghép nối thủ công (Match Memory Learning).
Tự động lưu các quyết định ghép nối của kỹ sư và ưu tiên sử dụng lại cho các lần sau.

TẠI SAO:
Trong thực tế dự toán M&E, có những mô tả viết tắt đặc thù hoặc cách gọi vật tư không chuẩn.
Khi kỹ sư đã chọn thủ công một lần, hệ thống cần ghi nhớ ngay để các lần chạy sau (hoặc dòng tương tự)
tự động nhận diện chính xác 100% mà không bắt người dùng chọn lại.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from core.normalizer import remove_vietnamese_accents, normalize_brand_name


class MatchMemory:
    """
    Quản lý lưu trữ và tra cứu lịch sử ghép nối thủ công.
    Dữ liệu được lưu dạng JSON bền vững tại thư mục gốc dự án.
    """
    def __init__(self, memory_file_path: Optional[str] = None):
        if memory_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_file_path = os.path.join(base_dir, "match_memory.json")
        self.memory_file_path = memory_file_path
        self.memories: Dict[str, Dict[str, Any]] = {}
        self.load()

    @staticmethod
    def generate_fingerprint(req_name: str, req_spec: str, req_brand: str) -> str:
        """
        Tạo khóa định danh (fingerprint) duy nhất cho yêu cầu vật tư.
        Chuẩn hóa chữ thường, bỏ dấu tiếng Việt, loại bỏ khoảng trắng thừa.
        """
        norm_name = remove_vietnamese_accents(req_name or "").lower()
        norm_spec = remove_vietnamese_accents(req_spec or "").lower()
        norm_brand = normalize_brand_name(req_brand or "")

        # Chuẩn hóa khoảng trắng và ký tự đặc biệt cơ bản
        clean_name = re.sub(r"\s+", " ", norm_name).strip()
        clean_spec = re.sub(r"\s+", " ", norm_spec).strip()
        
        return f"{norm_brand}|{clean_name}|{clean_spec}"

    def load(self) -> None:
        """Nạp dữ liệu bộ nhớ từ file JSON."""
        if os.path.exists(self.memory_file_path):
            try:
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception as e:
                print(f"[MatchMemory] Cảnh báo lỗi nạp file memory: {e}")
                self.memories = {}
        else:
            self.memories = {}

    def save(self) -> None:
        """Ghi dữ liệu bộ nhớ ra file JSON."""
        try:
            with open(self.memory_file_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MatchMemory] Lỗi lưu file memory: {e}")

    def record_match(
        self,
        req_name: str,
        req_spec: str,
        req_brand: str,
        item_id: int,
        item_code: str,
        item_name: str,
        item_spec: str,
        item_brand: str,
    ) -> None:
        """
        Ghi nhận một quyết định chọn vật tư thủ công từ kỹ sư.
        """
        fp = self.generate_fingerprint(req_name, req_spec, req_brand)
        self.memories[fp] = {
            "req_name": req_name,
            "req_spec": req_spec,
            "req_brand": req_brand,
            "target_item_id": item_id,
            "target_item_code": item_code,
            "target_item_name": item_name,
            "target_item_spec": item_spec,
            "target_item_brand": item_brand,
            "match_count": self.memories.get(fp, {}).get("match_count", 0) + 1,
        }
        self.save()

    def find_match(self, req_name: str, req_spec: str, req_brand: str) -> Optional[Dict[str, Any]]:
        """
        Tra cứu xem yêu cầu này đã từng được kỹ sư gán thủ công trước đây chưa.
        """
        fp = self.generate_fingerprint(req_name, req_spec, req_brand)
        return self.memories.get(fp)

    def delete_record(self, req_name: str, req_spec: str, req_brand: str) -> bool:
        """Xóa một bản ghi trong bộ nhớ."""
        fp = self.generate_fingerprint(req_name, req_spec, req_brand)
        if fp in self.memories:
            del self.memories[fp]
            self.save()
            return True
        return False

    @property
    def total_records(self) -> int:
        return len(self.memories)


# BIGCOM M&E CONTRACTOR - DỰ TOÁN CƠ ĐIỆN TỰ ĐỘNG (SMART MATCHING PRO)

Hệ thống tự động hóa lập dự toán và áp giá chào thầu chuyên dụng cho các nhà thầu Cơ Điện (M&E). 

Ứng dụng kết hợp phễu lọc 4 tầng, từ điển 9 phân hệ vật tư M&E đồng nghĩa và bộ 10 quy tắc nghiệp vụ chuyên sâu ngành điện - nước để tự động bóc tách quy cách, so khớp ứng viên chính xác và xuất file Excel hoàn thiện.

---

## 🌟 Tính Năng Nổi Bật

1. **Phễu so khớp 4 tầng chính xác**:
   - **Tầng 1 (Hãng sản xuất - Hard constraint)**: Bắt buộc chuẩn xác 100% hãng sản xuất (Cadisun, Tiền Phong, Schneider, Sino/SP, LS, Mitsubishi...). Tuyệt đối không chào nhầm hãng.
   - **Tầng 2 (Tên vật tư & 9 phân hệ)**: Sử dụng bộ từ điển đồng nghĩa (Synonyms) cho 9 phân hệ vật tư (Dây cáp, Ống luồn, Công tắc ổ cắm, Thang máng cáp, Đóng cắt, Cấp thoát nước, Van vòi, Ống đồng bảo ôn, Ống gió).
   - **Tầng 3 (Kích thước & Tiết diện)**: So khớp chuẩn tiết diện dây cáp (`4x35`, `1x70`), đường kính ống nước (`D20`, `DN50`), số cực và dòng định mức aptomat (`2P 16A`).
   - **Tầng 4 (Thuộc tính & Tiêu chuẩn)**: So khớp cấp điện áp, cấp chịu lửa (chống cháy FR/FRN), cấp áp lực ống (PN10, PN16, PN20).

2. **Bộ quy tắc nghiệp vụ dây & cáp điện chuyên sâu**:
   - Chuẩn hóa ký hiệu lõi `2C`, `3C`, `4C`, `5C` tương đương số lõi.
   - Phát hiện dạng cáp đơn kép `2x1c1.5` = 2 sợi 1x1.5 (tự động nhân đôi giá).
   - Dây/cáp tiếp địa: $<10\text{ mm}^2$ ưu tiên `VCSF`, $\ge 10\text{ mm}^2$ chọn `CV`.
   - Cáp có ký hiệu `FR`, `FRN`, chống cháy bắt buộc chọn `FRN-CXV`.
   - Tự động chuyển đổi `Cu/PVC/PVC` sang `CXV` khi điện áp $0.6/1\text{kV}$ hoặc vượt quy cách sản xuất.
   - **Quy tắc Upsize (Tiết diện lớn hơn gần nhất)**: Khi đã đúng hãng, đúng chủng loại nhưng catalog không có tiết diện yêu cầu, tự động chọn tiết diện lớn hơn gần nhất và **bôi đỏ font chữ cột Ghi chú** trong file Excel.
   - Dòng vật tư không tìm thấy: Tự động để trống thông số và đơn giá chào thầu, ghi chú `Không tìm thấy dữ liệu`.

3. **Hai phương thức vận hành linh hoạt**:
   - **Chế độ Web App độc lập (`BC_SMP.html`)**: Chạy trực tiếp trên trình duyệt (Edge, Chrome) không cần cài đặt server hay Python, kéo thả file DATA và FORM để áp giá tức thì.
   - **Chế độ Backend Python (`app.py` & `core/`)**: Chạy server Flask phục vụ mở rộng, API và xử lý dữ liệu lớn.

---

## 📁 Cấu Trúc Thư Mục

```
SMP BIGCOM/
├── BC_SMP.html                 # Ứng dụng Web độc lập (chạy trực tiếp không cần server)
├── app.py                      # Flask Web Server
├── Chay_Webapp.bat             # File khởi động nhanh Web Server trên Windows
├── DATA BIGCOM.xlsx            # Cơ sở dữ liệu giá vật tư chuẩn của Bigcom
├── FORM BÁO GIÁ.xlsx           # Mẫu hồ sơ mời thầu cần áp giá
├── Quy_tac.md                  # Tài liệu chi tiết các quy tắc nghiệp vụ M&E
├── core/
│   ├── dynamic_loader.py       # Tự động nạp và lập chỉ mục đa sheet dữ liệu
│   ├── normalizer.py           # Bóc tách thông số kỹ thuật, chuẩn hóa tiếng Việt, hãng
│   ├── matcher.py              # Bộ máy so khớp phễu 4 tầng & thuật toán Upsize
│   └── excel_exporter.py       # Xuất file Excel định dạng bảng chuẩn, kẻ viền và bôi màu
├── templates/
│   └── index.html              # Giao diện web Flask
└── exports/                    # Thư mục chứa các file Excel báo giá đã xuất
```

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Sử dụng trực tiếp Web App độc lập
1. Nhấp đúp chuột vào file **`BC_SMP.html`** để mở trên trình duyệt web.
2. Kéo thả file **`DATA BIGCOM.xlsx`** vào ô số 1.
3. Kéo thả file **`FORM BÁO GIÁ.xlsx`** vào ô số 2.
4. Bấm nút **⚡ Áp Giá Tự Động**.
5. Bấm **📥 Xuất File Excel** để tải về bảng báo giá hoàn chỉnh đã áp giá và định dạng màu.

### Cách 2: Chạy Web Server Flask
1. Cài đặt các thư viện Python:
   ```bash
   pip install flask openpyxl
   ```
2. Chạy ứng dụng:
   ```bash
   python app.py
   # hoặc nhấp đúp file Chay_Webapp.bat
   ```
3. Mở trình duyệt tại: `http://localhost:5000`

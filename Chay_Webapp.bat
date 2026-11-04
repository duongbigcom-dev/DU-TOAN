@echo off
chcp 65001 >nul
title DỰ TOÁN CƠ ĐIỆN M&E - SMART MATCHING PRO V2.7.8
color 0B

echo ======================================================================
echo    PHẦN MỀM ÁP GIÁ TỰ ĐỘNG DỰ TOÁN CƠ ĐIỆN M&E (SMART MATCHING PRO)
echo ======================================================================
echo.

cd /d "E:\SMP BIGCOM"

set PYTHON_CMD=python
if exist "C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe"
)

echo [*] Đang kiểm tra môi trường Python...
"%PYTHON_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo [!] Không tìm thấy Python 3.11 trên máy tính.
    echo [*] Vui lòng cài đặt Python hoặc liên hệ hỗ trợ.
    pause
    exit /b
)

echo [*] Môi trường Python hợp lệ!
echo [*] Đang khởi động Web App tại địa chỉ: http://127.0.0.1:5000 ...
echo [*] Trình duyệt sẽ tự động mở sau 3 giây...
echo.

start "" http://127.0.0.1:5000
"%PYTHON_CMD%" app.py

pause


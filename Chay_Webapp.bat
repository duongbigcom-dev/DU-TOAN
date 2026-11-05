@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title DỰ TOÁN CƠ ĐIỆN M^&E - BIGCOM SMART MATCHING PRO V2.8
color 0B

echo ======================================================================
echo    CÔNG TY CƠ ĐIỆN BIGCOM - HỆ THỐNG DỰ TOÁN ÁP GIÁ TỰ ĐỘNG
echo                   SMART MATCHING PRO V2.8
echo ======================================================================
echo.

REM 1. Chuyển thư mục làm việc về thư mục chứa file .bat
cd /d "%~dp0"

REM 2. Tự động dò tìm đường dẫn Python hợp lệ
set "PYTHON_CMD="

REM Ưu tiên các đường dẫn cài đặt trực tiếp của người dùng
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto found_python
)

REM Kiểm tra Program Files hoặc C:\Python
if exist "C:\Program Files\Python311\python.exe" (
    set "PYTHON_CMD=C:\Program Files\Python311\python.exe"
    goto found_python
)
if exist "C:\Program Files\Python312\python.exe" (
    set "PYTHON_CMD=C:\Program Files\Python312\python.exe"
    goto found_python
)
if exist "C:\Python311\python.exe" (
    set "PYTHON_CMD=C:\Python311\python.exe"
    goto found_python
)
if exist "C:\Python312\python.exe" (
    set "PYTHON_CMD=C:\Python312\python.exe"
    goto found_python
)

REM Kiểm tra qua py launcher nếu có
for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
    set "PYTHON_CMD=%%I"
    goto found_python
)

REM Kiểm tra python trên biến môi trường PATH
for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)" 2^>nul') do (
    set "PYTHON_CMD=%%I"
    goto found_python
)

:found_python
if not defined PYTHON_CMD goto python_not_found

echo [*] Đang kiểm tra môi trường Python...
echo [*] Tìm thấy Python tại: "%PYTHON_CMD%"
"%PYTHON_CMD%" --version
echo.

REM 3. Kiểm tra thư viện cần thiết
echo [*] Đang kiểm tra thư viện Flask và Openpyxl...
"%PYTHON_CMD%" -c "import flask, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [*] Đang tự động cài đặt thư viện flask và openpyxl...
    "%PYTHON_CMD%" -m pip install flask openpyxl
    if errorlevel 1 (
        echo [!] Cài đặt thư viện thất bại. Đang mở Web App độc lập BC_SMP.html...
        start "" "%~dp0BC_SMP.html"
        pause
        exit /b 1
    )
)
echo [*] Thư viện đã sẵn sàng!
echo.

REM 4. Khởi động Web App (app.py sẽ tự động mở trình duyệt web)
echo [*] Đang khởi động Web App máy chủ...
echo [*] Trình duyệt web sẽ tự động mở ngay khi máy chủ sẵn sàng!
echo.
echo (Nhấn Ctrl+C trong cửa sổ này nếu muốn dừng máy chủ)
echo ======================================================================
echo.

"%PYTHON_CMD%" app.py

REM 5. Nếu máy chủ gặp sự cố dừng đột ngột, tự động mở file HTML độc lập
if errorlevel 1 (
    echo.
    echo ======================================================================
    echo [!] Máy chủ gặp sự cố dừng đột ngột.
    echo [*] Đang tự động mở bản Web App độc lập BC_SMP.html trên trình duyệt...
    echo ======================================================================
    start "" "%~dp0BC_SMP.html"
)

pause
exit /b 0

:python_not_found
echo ======================================================================
echo [!] KHÔNG TÌM THẤY PYTHON TRÊN MÁY TÍNH!
echo ======================================================================
echo.
echo Bạn có thể chọn một trong các lựa chọn sau:
echo.
echo  [1] Tự động cài đặt Python 3.11 ngay bây giờ qua winget
echo  [2] Mở ngay bản Web App độc lập BC_SMP.html (chạy trực tiếp trên trình duyệt)
echo  [3] Thoát
echo.
set /p CHOICE="Nhập lựa chọn [1/2/3] rồi nhấn Enter: "

if "%CHOICE%"=="1" (
    echo.
    echo [*] Đang tải và cài đặt Python 3.11... Vui lòng chờ...
    winget install Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements
    echo.
    echo [*] Cài đặt hoàn tất! Vui lòng chạy lại file Chay_Webapp.bat.
    pause
    exit /b 0
)

if "%CHOICE%"=="2" (
    echo.
    echo [*] Đang mở Web App độc lập BC_SMP.html trên trình duyệt...
    start "" "%~dp0BC_SMP.html"
    exit /b 0
)

exit /b 1

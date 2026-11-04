@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title DU TOAN CO DIEN M^&E - SMART MATCHING PRO V2.7.8
color 0B

echo ======================================================================
echo    PHAN MEM AP GIA TU DONG DU TOAN CO DIEN M^&E (SMART MATCHING PRO)
echo ======================================================================
echo.

REM 1. Chuyen thu muc lam viec ve thu muc chua file .bat
cd /d "%~dp0"

REM 2. Tu dong do tim duong dan Python hop le
set "PYTHON_CMD="

REM Uu tien cac duong dan cai dat truc tiep cua nguoi dung
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

REM Kiem tra Program Files hoac C:\Python
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

REM Kiem tra qua py launcher neu co
for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
    set "PYTHON_CMD=%%I"
    goto found_python
)

REM Kiem tra python tren bien moi truong PATH
for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)" 2^>nul') do (
    set "PYTHON_CMD=%%I"
    goto found_python
)

:found_python
if not defined PYTHON_CMD goto python_not_found

echo [*] Dang kiem tra moi truong Python...
echo [*] Tim thay Python tai: "%PYTHON_CMD%"
"%PYTHON_CMD%" --version
echo.

REM 3. Kiem tra thu vien can thiet
echo [*] Dang kiem tra thu vien Flask va Openpyxl...
"%PYTHON_CMD%" -c "import flask, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [*] Dang tu dong cai dat thu vien flask va openpyxl...
    "%PYTHON_CMD%" -m pip install flask openpyxl
    if errorlevel 1 (
        echo [!] Cai dat thu vien that bai. Vui long kiem tra ket noi mang.
        pause
        exit /b 1
    )
)
echo [*] Thu vien da san sang!
echo.

REM 4. Khoi dong Web App va mo trinh duyet
echo [*] Dang khoi dong Web App tai dia chi: http://127.0.0.1:5000 ...
echo [*] Trinh duyet se tu dong mo sau 2 giay...
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"
"%PYTHON_CMD%" app.py

pause
exit /b 0

:python_not_found
echo ======================================================================
echo [!] KHONG TIM THAY PYTHON TREN MAY TINH!
echo ======================================================================
echo.
echo Ban co the chon mot trong cac lua chon sau:
echo.
echo  [1] Tu dong cai dat Python 3.11 ngay bay gio qua winget
echo  [2] Mo ban Web App doc lap BC_SMP.html tren trinh duyet
echo  [3] Thoat
echo.
set /p CHOICE="Nhap lua chon [1/2/3] roi nhan Enter: "

if "%CHOICE%"=="1" (
    echo.
    echo [*] Dang tai va cai dat Python 3.11... Vui long cho...
    winget install Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements
    echo.
    echo [*] Cai dat hoan tat! Vui long chay lai file Chay_Webapp.bat.
    pause
    exit /b 0
)

if "%CHOICE%"=="2" (
    echo.
    echo [*] Dang mo Web App doc lap BC_SMP.html tren trinh duyet...
    start "" "BC_SMP.html"
    exit /b 0
)

exit /b 1

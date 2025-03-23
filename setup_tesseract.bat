@echo off
echo Checking Tesseract installation...
echo.

where tesseract >nul 2>nul
if %errorlevel% equ 0 (
    echo Tesseract is installed and in PATH
    echo Version information:
    tesseract --version
) else (
    echo Tesseract is not installed or not in PATH
    echo.
    echo Please follow these steps:
    echo 1. Download Tesseract installer from:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Run the installer AS ADMINISTRATOR
    echo 3. During installation:
    echo    - Choose installation path: C:\Program Files\Tesseract-OCR
    echo    - CHECK the box 'Add to system PATH'
    echo 4. Click Install and wait for completion
    echo 5. RESTART your computer
    echo.
    echo After installation, run this script again to verify.
)

echo.
echo Press any key to exit...
pause >nul 
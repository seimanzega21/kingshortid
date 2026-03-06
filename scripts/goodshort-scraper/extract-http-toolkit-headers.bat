@echo off
echo.
echo ============================================================================
echo   HTTP Toolkit - Video Download Test
echo ============================================================================
echo.
echo This script will help you download video segments using HTTP Toolkit.
echo.
echo BEFORE RUNNING THIS:
echo   1. HTTP Toolkit must be connected (green status)
echo   2. Play a video in GoodShort app (let it buffer 10+ seconds)
echo   3. Copy .ts request as cURL from HTTP Toolkit
echo   4. Save cURL to: curl_export.txt
echo.
echo ============================================================================
echo.

if not exist "curl_export.txt" (
    echo ERROR: curl_export.txt not found!
    echo.
    echo Steps to create curl_export.txt:
    echo   1. Open HTTP Toolkit
    echo   2. Play video in emulator
    echo   3. Find .ts request with status 200 OK
    echo   4. Right-click and select "Copy as cURL"
    echo   5. Paste to curl_export.txt in this folder
    echo.
    pause
    exit /b 1
)

echo [1/2] Extracting headers from cURL...
echo.
python download_with_http_toolkit.py --parse-curl curl_export.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to parse cURL
    echo Make sure curl_export.txt contains FULL cURL command
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   Headers extracted successfully!
echo ============================================================================
echo.
echo Saved to: http_toolkit_headers.json
echo.
echo Next steps:
echo   1. Test download: python download_with_http_toolkit.py --drama-folder test_output\jenderal_jadi_tukang
echo   2. Or download real drama after processing production data
echo.
pause

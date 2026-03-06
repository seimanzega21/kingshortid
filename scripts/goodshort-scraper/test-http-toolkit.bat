@echo off
echo.
echo ============================================================================
echo   HTTP TOOLKIT TEST - Quick Segment Capture Test
echo ============================================================================
echo.

echo [STEP 1] Setup HTTP Toolkit
echo.
echo    1. Download HTTP Toolkit dari: https://httptoolkit.com/
echo    2. Install and launch HTTP Toolkit
echo    3. Click "Android Device via ADB"
echo    4. Wait for certificate installation
echo.
echo Press any key when HTTP Toolkit shows "Intercepting Android device"...
pause
echo.

echo [STEP 2] Manual Test - Play 1 Episode
echo.
echo    1. Open GoodShort app on device
echo    2. Navigate to "Jenderal Jadi Tukang"
echo    3. Play Episode 1
echo    4. Let it buffer for 30 seconds
echo.
echo Press any key after video has played for 30 seconds...
pause
echo.

echo [STEP 3] Check HTTP Toolkit
echo.
echo    Look for requests in HTTP Toolkit that contain:
echo    - URL contains ".ts" 
echo    - Domain: goodreels.com
echo    - Response: video/MP2T
echo.
echo    Did you see .ts segment URLs? (Y/N)
set /p RESULT="Enter Y or N: "

if /i "%RESULT%"=="Y" (
    echo.
    echo ============================================================================
    echo   SUCCESS! .ts URLs are visible in HTTP Toolkit
    echo ============================================================================
    echo.
    echo Next Steps:
    echo   1. Export the captured requests from HTTP Toolkit
    echo   2. Run: python parse_toolkit_export.py
    echo   3. Download segments automatically
    echo.
    echo Ready for full automation? Run: .\capture_with_toolkit.bat
    echo.
) else (
    echo.
    echo ============================================================================
    echo   No .ts URLs found - Troubleshooting
    echo ============================================================================
    echo.
    echo Possible issues:
    echo   1. App not using system proxy
    echo      Solution: Reinstall HTTP Toolkit certificate
    echo.
    echo   2. Certificate not trusted
    echo      Solution: Check Android Settings ^> Security ^> Trusted credentials
    echo.
    echo   3. App using certificate pinning
    echo      Solution: Need to disable pinning with Frida
    echo.
    echo Try:
    echo   - Restart app
    echo   - Reinstall HTTP Toolkit connection
    echo   - Check proxy settings in Android
    echo.
)

pause

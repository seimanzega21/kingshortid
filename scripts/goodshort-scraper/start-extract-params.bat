@echo off
echo ========================================
echo  Extract Device Parameters for API
echo ========================================
echo.
echo This script will extract:
echo   - GAID (Google Advertising ID)
echo   - Android Device ID
echo   - APK Signature MD5
echo   - User Token (after login)
echo.
echo Instructions:
echo 1. Make sure GoodShort app is running on device
echo 2. This script will hook into the app
echo 3. Use the app normally (browse, login if needed)
echo 4. Parameters will be captured automatically
echo 5. Copy the exported JSON at the end
echo.
pause

frida -U -f com.newreading.goodreels -l frida/extract-device-params.js --no-pause

@echo off
echo ========================================
echo GoodShort Frida Capture - Auto Restart
echo ========================================
echo.
echo Checking if GoodShort app is running...

REM Kill app first to ensure clean start
adb shell am force-stop com.newreading.goodreels 2>nul

echo Starting GoodShort app with Frida...
echo.
echo [!] Browse dramas and tap episodes in the app
echo [!] Frida will auto-capture URLs
echo.
echo Commands in Frida console:
echo   status()     - Show capture stats
echo   list()       - List all dramas
echo   exportData() - Export JSON
echo.
echo ========================================
echo.

REM Start Frida with spawn mode (-f) to auto-launch the app
frida -U -f com.newreading.goodreels -l frida\capture-autosave.js

pause

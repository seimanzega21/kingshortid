@echo off
REM Quick launcher for Frida signing hook

echo Starting Frida hook for GoodShort signing...
echo.
echo Make sure:
echo   1. Android device/emulator is connected
echo   2. Frida server is running on device
echo   3. GoodShort app is installed
echo.

REM Get GoodShort package name
set PACKAGE=com.goodshort

echo Attaching to %PACKAGE%...
frida -U -l frida\hook_signing.js -f %PACKAGE% --no-pause

pause

@echo off
echo ========================================
echo Extract GoodShort APK from LDPlayer
echo ========================================
echo.

REM LDPlayer default adb port is 5555
echo [1/5] Connecting to LDPlayer...
adb connect 127.0.0.1:5555
timeout /t 2 /nobreak >nul
echo.

echo [2/5] Checking connection...
adb devices
echo.

echo [3/5] Finding GoodShort package...
adb shell pm list packages | findstr good
echo.

set PACKAGE=com.newreading.goodreels
echo Using package: %PACKAGE%
echo.

echo [4/5] Getting APK path...
for /f "tokens=2 delims=:" %%a in ('adb shell pm path %PACKAGE%') do set APK_PATH=%%a
REM Remove spaces
set APK_PATH=%APK_PATH: =%
echo APK Path: %APK_PATH%
echo.

echo [5/5] Pulling APK (this may take 1-2 minutes)...
adb pull %APK_PATH% goodshort.apk
echo.

if exist goodshort.apk (
    echo.
    echo ========================================
    echo SUCCESS! 
    echo ========================================
    dir goodshort.apk
    echo.
    echo APK saved as: goodshort.apk
    echo Size: 
    for %%A in (goodshort.apk) do echo %%~zA bytes
    echo.
    echo NEXT STEP:
    echo 1. Open jadx-gui
    echo 2. File ^> Open File ^> Select goodshort.apk
    echo 3. Wait for decompilation (2-5 mins)
    echo.
) else (
    echo ========================================
    echo FAILED to extract APK
    echo ========================================
    echo.
    echo Troubleshooting:
    echo 1. Make sure LDPlayer is running
    echo 2. Try: adb connect 127.0.0.1:5555
    echo 3. Check adb devices shows device
)

pause

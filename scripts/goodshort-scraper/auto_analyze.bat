@echo off
echo ========================================
echo Automated APK Analysis  
echo ========================================
echo.

set APKPATH=goodshort.apk
set JADX_PATH=C:\Users\Seiman\Downloads\jadx-gui-1.5.0-with-jre-win\bin\jadx.bat
set OUTPUT_DIR=goodshort_decompiled

echo [1/3] Checking files...
if not exist %APKPATH% (
    echo ERROR: goodshort.apk not found!
    pause
    exit /b 1
)

echo [2/3] Decompiling APK with jadx (2-3 minutes)...
echo Output: %OUTPUT_DIR%
echo.

if exist "%JADX_PATH%" (
    "%JADX_PATH%" -d %OUTPUT_DIR% %APKPATH% --show-bad-code
) else (
    echo jadx not found at expected location, trying PATH...
    jadx -d %OUTPUT_DIR% %APKPATH% --show-bad-code
)

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Decompilation failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Decompilation complete!
echo.
echo Decompiled code saved to: %OUTPUT_DIR%\sources
echo.
echo Now searching for signing code...
echo.

REM Search for signing-related files
cd %OUTPUT_DIR%\sources

echo Searching for Sign/Crypto classes in com.newreading...
dir /s /b *Sign*.java | findstr /i "newreading goodreels" > ..\..\sign_files.txt
dir /s /b *Crypto*.java | findstr /i "newreading goodreels" >> ..\..\sign_files.txt
dir /s /b *Request*.java | findstr /i "newreading goodreels" | findstr /i "sign request" >> ..\..\sign_files.txt

cd ..\..

echo.
echo Results saved to: sign_files.txt
echo.

if exist sign_files.txt (
    echo Found files:
    type sign_files.txt
) else (
    echo No sign-related files found in newreading package
)

echo.
echo ========================================
echo Next: Check specific files manually
echo ========================================

pause

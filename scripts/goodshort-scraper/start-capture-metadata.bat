@echo off
echo ====================================================
echo GoodShort Metadata Capture - Indonesian Focus
echo ====================================================
echo.
echo This will:
echo  1. Launch GoodShort app with Frida
echo  2. Capture video URLs
echo  3. Capture cover images
echo  4. Capture full metadata (Indonesian titles, descriptions)
echo.
echo INSTRUCTIONS:
echo  - Browse dramas in the GoodShort app
echo  - Select dramas WITH INDONESIAN TITLES  
echo  - Tap 10-15 episodes per drama
echo  - When done, type: exportData()
echo.
pause

cd /d "%~dp0"
frida -U -f com.newreading.goodreels -l frida\capture-autosave.js

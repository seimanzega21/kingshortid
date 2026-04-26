@echo off
echo ==================================================
echo  MEMULAI CHROME UNTUK BYPASS CLOUDFLARE
echo ==================================================
echo.
echo Menjalankan Google Chrome dengan mode Debugging (Port 9222)...
echo.
echo PENTING:
echo 1. Pastikan TIDAK ADA jendela Chrome lain yang sedang terbuka!
echo 2. Login ke akun VIP Vidrama di jendela yang baru terbuka ini.
echo 3. Setelah login sukses, biarkan jendela ini tetap terbuka.
echo 4. Jalankan script python scrape_shortmax_vip.py di terminal lain.
echo.
pause

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%temp%\chrome_dev_profile_vidrama" "https://vidrama.asia/provider/shortmax"

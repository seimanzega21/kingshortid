# Panduan Menjalankan StardustTV Scraper

## Persiapan

Semua sudah ready! Anda hanya perlu menjalankan script.

## Langkah-Langkah

### 1. Buka PowerShell

Tekan `Win + X` lalu pilih **Windows PowerShell** atau **Terminal**

### 2. Masuk ke Folder Scraper

```powershell
cd d:\kingshortid\scripts\stardusttv-scraper
```

### 3. Jalankan Scraper

```powershell
python selenium_scraper.py
```

## Apa Yang Akan Terjadi

1. **Chrome browser akan terbuka otomatis** (jangan ditutup!)
2. Script akan coba login dengan akun VIP Anda
3. Browser akan buka halaman drama
4. Script akan extract M3U8 video URL
5. Browser akan tetap buka selama 10 detik untuk Anda lihat hasilnya
6. Browser akan tutup otomatis

## Yang Perlu Diperhatikan

✅ **Biarkan browser terbuka** - jangan ditutup manual
✅ **Tunggu sampai selesai** - prosesnya sekitar 30-60 detik untuk 1 drama
✅ **Lihat terminal** untuk progress log

## Hasil Yang Diharapkan

Di terminal, Anda akan lihat:
```
[+] Title: Dumped Him Married The Warlord Episode 1
[+] M3U8 URL found: https://...
[+] INDONESIAN SUBTITLE DETECTED!
```

Jika lihat pesan **"INDONESIAN SUBTITLE DETECTED!"** berarti berhasil! ✅

## Jika Ada Masalah

### Chrome tidak terbuka
```powershell
pip install selenium webdriver-manager
```

### Login gagal
Cek file `.env` punya credentials yang benar:
```
STARDUSTTV_EMAIL=stardustlovers977@gmail.com
STARDUSTTV_PASSWORD=Stardust1010@
```

### 403 Error / Rate Limit
Tunggu 1-2 jam, lalu coba lagi. IP Anda mungkin kena temporary limit.

## Setelah Test Berhasil

Jika test 1 drama berhasil, kita bisa lanjut scrape **semua 38 drama** dengan script batch.

Kabari saya hasilnya ya bro! 🚀

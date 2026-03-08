/**
 * Static HTML pages for Google Play compliance
 * Privacy Policy + Account Deletion pages
 */

export const privacyPolicyHtml = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kebijakan Privasi — KingShort</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0a0a; color: #e5e5e5; font-family: system-ui, -apple-system, sans-serif; padding: 40px 20px; line-height: 1.7; }
    .container { max-width: 720px; margin: 0 auto; }
    h1 { color: #FFD700; font-size: 28px; margin-bottom: 8px; }
    .date { color: #9CA3AF; font-size: 14px; margin-bottom: 32px; }
    h2 { color: #fff; font-size: 18px; margin-bottom: 12px; }
    .section { margin-bottom: 32px; color: #d1d5db; font-size: 15px; }
    ul, ol { padding-left: 20px; line-height: 2; }
    strong { color: #fff; }
    a { color: #FFD700; }
    .footer { border-top: 1px solid #333; margin-top: 48px; padding-top: 24px; text-align: center; color: #666; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Kebijakan Privasi</h1>
    <p class="date">Terakhir diperbarui: 21 Februari 2026</p>

    <div class="section">
      <h2>1. Pendahuluan</h2>
      <p>KingShort ("kami", "aplikasi") berkomitmen melindungi privasi pengguna. Kebijakan ini menjelaskan bagaimana kami mengumpulkan, menggunakan, dan melindungi informasi Anda saat menggunakan aplikasi KingShort.</p>
    </div>

    <div class="section">
      <h2>2. Data yang Kami Kumpulkan</h2>
      <ul>
        <li><strong>Informasi Akun:</strong> Email dan kata sandi (jika mendaftar). Akun tamu menggunakan ID perangkat anonim.</li>
        <li><strong>Data Penggunaan:</strong> Riwayat tontonan, episode yang ditonton, dan preferensi konten untuk personalisasi.</li>
        <li><strong>Device ID:</strong> Identifikasi perangkat anonim untuk login tamu dan fungsionalitas aplikasi.</li>
        <li><strong>Push Notification Token:</strong> Token perangkat untuk mengirim notifikasi (opsional, bisa dinonaktifkan).</li>
      </ul>
    </div>

    <div class="section">
      <h2>3. Bagaimana Kami Menggunakan Data</h2>
      <ul>
        <li>Menyediakan dan meningkatkan layanan streaming</li>
        <li>Personalisasi rekomendasi konten</li>
        <li>Mengelola akun pengguna dan sistem koin</li>
        <li>Mengirim notifikasi tentang konten baru (jika diizinkan)</li>
        <li>Analitik internal untuk peningkatan aplikasi</li>
      </ul>
    </div>

    <div class="section">
      <h2>4. Penyimpanan dan Keamanan Data</h2>
      <p>Data Anda disimpan dengan aman menggunakan enkripsi standar industri. Token autentikasi disimpan secara lokal di perangkat Anda menggunakan penyimpanan aman (Secure Store). Kami tidak menjual atau membagikan data pribadi Anda kepada pihak ketiga untuk tujuan pemasaran.</p>
    </div>

    <div class="section">
      <h2>5. Hak Pengguna</h2>
      <ul>
        <li><strong>Akses:</strong> Anda dapat melihat data profil Anda di pengaturan aplikasi.</li>
        <li><strong>Penghapusan:</strong> Anda dapat menghapus akun dan semua data terkait melalui menu Pengaturan di aplikasi atau dengan menghubungi kami.</li>
        <li><strong>Notifikasi:</strong> Anda dapat menonaktifkan notifikasi kapan saja melalui pengaturan.</li>
        <li><strong>Riwayat:</strong> Anda dapat menghapus riwayat tontonan dari halaman Daftar Saya.</li>
      </ul>
    </div>

    <div class="section">
      <h2>6. Layanan Pihak Ketiga</h2>
      <p>Aplikasi dapat menggunakan layanan pihak ketiga berikut:</p>
      <ul>
        <li>Google Sign-In — untuk autentikasi</li>
        <li>Google AdMob — untuk iklan</li>
        <li>Expo Push Notifications — untuk notifikasi</li>
        <li>Cloudflare — untuk hosting dan CDN</li>
      </ul>
      <p>Setiap layanan memiliki kebijakan privasi mereka sendiri.</p>
    </div>

    <div class="section">
      <h2>7. Anak-Anak</h2>
      <p>KingShort tidak ditujukan untuk anak di bawah 13 tahun. Kami tidak secara sengaja mengumpulkan data dari anak-anak. Jika Anda mengetahui bahwa anak di bawah 13 tahun telah memberikan data pribadi kepada kami, silakan hubungi kami untuk penghapusan.</p>
    </div>

    <div class="section">
      <h2>8. Perubahan Kebijakan</h2>
      <p>Kami dapat memperbarui kebijakan ini dari waktu ke waktu. Perubahan akan diberitahukan melalui aplikasi atau halaman ini. Penggunaan aplikasi setelah perubahan berarti Anda menyetujui kebijakan yang diperbarui.</p>
    </div>

    <div class="section">
      <h2>9. Hubungi Kami</h2>
      <p>Jika Anda memiliki pertanyaan tentang kebijakan privasi ini, hubungi kami di:<br><br>📧 <a href="mailto:cs.kingshort@gmail.com">cs.kingshort@gmail.com</a></p>
    </div>

    <div class="footer">© 2026 KingShort. All rights reserved.</div>
  </div>
</body>
</html>`;

export const deleteAccountHtml = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hapus Akun — KingShort</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0a0a; color: #e5e5e5; font-family: system-ui, -apple-system, sans-serif; padding: 40px 20px; line-height: 1.7; }
    .container { max-width: 720px; margin: 0 auto; }
    h1 { color: #FFD700; font-size: 28px; margin-bottom: 8px; }
    .date { color: #9CA3AF; font-size: 14px; margin-bottom: 32px; }
    h2 { color: #fff; font-size: 18px; margin-bottom: 12px; }
    .section { margin-bottom: 32px; color: #d1d5db; font-size: 15px; }
    ul, ol { padding-left: 20px; line-height: 2; }
    strong { color: #fff; }
    a { color: #FFD700; }
    .footer { border-top: 1px solid #333; margin-top: 48px; padding-top: 24px; text-align: center; color: #666; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Penghapusan Akun</h1>
    <p class="date">Terakhir diperbarui: 8 Maret 2026</p>

    <div class="section">
      <h2>Cara Menghapus Akun</h2>
      <p>Anda dapat menghapus akun KingShort Anda dengan mengikuti langkah-langkah berikut:</p>
      <ol>
        <li>Buka aplikasi <strong>KingShort</strong></li>
        <li>Masuk ke tab <strong>Profil</strong></li>
        <li>Ketuk <strong>Pengaturan</strong> (ikon ⚙️)</li>
        <li>Scroll ke bawah dan ketuk <strong>"Hapus Akun"</strong></li>
        <li>Konfirmasi penghapusan akun Anda</li>
      </ol>
    </div>

    <div class="section">
      <h2>Melalui Email</h2>
      <p>Jika Anda tidak dapat mengakses aplikasi, Anda dapat meminta penghapusan akun dengan mengirim email ke:</p>
      <p><br>📧 <a href="mailto:cs.kingshort@gmail.com">cs.kingshort@gmail.com</a></p>
      <p><br>Sertakan informasi berikut dalam email Anda:</p>
      <ul>
        <li>Alamat email yang terdaftar di akun KingShort Anda</li>
        <li>Alasan penghapusan (opsional)</li>
      </ul>
    </div>

    <div class="section">
      <h2>Data yang Akan Dihapus</h2>
      <p>Saat Anda menghapus akun, data berikut akan dihapus secara permanen:</p>
      <ul>
        <li><strong>Profil pengguna</strong> — nama, email, foto profil</li>
        <li><strong>Saldo koin</strong> — semua koin yang belum digunakan</li>
        <li><strong>Riwayat tontonan</strong> — daftar episode yang pernah ditonton</li>
        <li><strong>Data check-in</strong> — streak dan riwayat check-in harian</li>
        <li><strong>Riwayat transaksi</strong> — semua log transaksi koin</li>
        <li><strong>Daftar bookmark</strong> — drama yang disimpan</li>
      </ul>
    </div>

    <div class="section">
      <h2>Waktu Pemrosesan</h2>
      <p>Penghapusan akun akan diproses dalam waktu <strong>maksimal 7 hari kerja</strong> setelah permintaan dikonfirmasi. Setelah dihapus, data tidak dapat dipulihkan.</p>
    </div>

    <div class="section">
      <h2>Hubungi Kami</h2>
      <p>Jika Anda memiliki pertanyaan tentang penghapusan akun, hubungi kami di:<br><br>📧 <a href="mailto:cs.kingshort@gmail.com">cs.kingshort@gmail.com</a></p>
    </div>

    <div class="footer">© 2026 KingShort. All rights reserved.</div>
  </div>
</body>
</html>`;

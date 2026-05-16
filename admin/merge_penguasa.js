const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const targetDir = 'D:\\Video_Drama';

// Konfigurasi pembagian part video
const parts = [
  { name: 'Part 1 (eps 1-10)', start: 1, end: 10 },
  { name: 'Part 2 (eps 11-20)', start: 11, end: 20 },
  { name: 'Part 3 (eps 21-30)', start: 21, end: 30 },
  { name: 'Part 4 (eps 31-40)', start: 31, end: 40 },
  { name: 'Part 5 (eps 41-50)', start: 41, end: 50 },
  { name: 'Part 6 (eps 51-60)', start: 51, end: 60 },
  { name: 'Part 7 (eps 61-70)', start: 61, end: 70 },
  { name: 'Part 8 (eps 71-85)', start: 71, end: 85 }
];

console.log('Memulai proses penggabungan video...');

// Cek apakah FFmpeg terinstall
try {
  execSync('ffmpeg -version', { stdio: 'ignore' });
} catch (e) {
  console.error("❌ FFmpeg tidak ditemukan! Pastikan FFmpeg sudah terinstal dan masuk ke Environment Variables (PATH) sistem Windows kamu.");
  process.exit(1);
}

for (const part of parts) {
  console.log(`\nMemproses ${part.name}...`);
  const listPath = path.join(targetDir, 'list.txt');
  const outputPath = path.join(targetDir, `${part.name}.mp4`);
  
  if (fs.existsSync(outputPath)) {
    console.log(`⏩ ${part.name} sudah ada, dilewati.`);
    continue;
  }

  let listContent = '';
  let validFilesCount = 0;
  
  for (let i = part.start; i <= part.end; i++) {
    const fileName = `Aku_Penguasa_Abadi_Ep_${i.toString().padStart(3, '0')}.mp4`;
    const filePath = path.join(targetDir, fileName);
    
    if (fs.existsSync(filePath)) {
      // Format file list untuk FFmpeg, kita jalankan di CWD targetDir jadi cukup pakai nama filenya
      listContent += `file '${fileName}'\n`;
      validFilesCount++;
    } else {
      console.log(`⚠️ Peringatan: File ${fileName} tidak ditemukan.`);
    }
  }
  
  if (validFilesCount === 0) {
    console.log(`❌ Tidak ada video untuk ${part.name}, dilewati.`);
    continue;
  }
  
  // Tulis file list.txt
  fs.writeFileSync(listPath, listContent);
  
  // Jalankan ffmpeg dengan codec copy (sangat cepat dan tanpa render ulang)
  try {
    const cmd = `ffmpeg -f concat -safe 0 -i list.txt -c copy "${part.name}.mp4"`;
    console.log(`🛠️ Menggabungkan ${validFilesCount} episode (tanpa rendering ulang, ini akan sangat cepat)...`);
    
    // Jalankan dengan working directory di folder D:\Video_Drama
    execSync(cmd, { cwd: targetDir, stdio: 'inherit' });
    
    console.log(`✅ ${part.name} berhasil dibuat!`);
  } catch (err) {
    console.error(`❌ Gagal memproses ${part.name}:`, err.message);
  }
  
  // Hapus file list.txt sementara
  if (fs.existsSync(listPath)) {
    fs.unlinkSync(listPath);
  }
}

console.log('\n🎉 Semua proses penggabungan video telah selesai! Silakan cek di folder D:\\Video_Drama');

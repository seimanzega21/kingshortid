const { execSync } = require('child_process');
const fs = require('fs');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
require('dotenv').config();

const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});

const BUCKET = process.env.R2_BUCKET_NAME;

async function uploadToR2(filePath, s3Key) {
    const fileStream = fs.createReadStream(filePath);
    await s3.send(new PutObjectCommand({
        Bucket: BUCKET,
        Key: s3Key,
        Body: fileStream,
        ContentType: 'video/mp4'
    }));
}

async function convertAndUpload() {
    try {
        console.log("1. Mengambil data episode dari API...");
        // Gunakan import() dinamis untuk node-fetch agar kompatibel dengan ES modules jika diperlukan,
        // atau fallback ke fetch bawaan Node 18+
        const fetchFn = typeof fetch === 'undefined' ? (await import('node-fetch')).default : fetch;
        
        const res = await fetchFn('https://api.shortlovers.id/api/dramas/cmlficdom00mbldfk2mieyiei/episodes');
        const episodes = await res.json();
        
        const missing540p = episodes.filter(ep => !ep.videoUrl540p);
        
        console.log(`Ditemukan ${missing540p.length} episode yang belum punya 540p.`);
        
        for (const ep of missing540p) {
            console.log(`\n--- Memproses Episode ${ep.episodeNumber} ---`);
            const sourceUrl = ep.videoUrl;
            
            // Ekstrak angka episode dari URL asli untuk R2 Key
            // Contoh URL: https://stream.shortlovers.id/melolo/dari-miskin-jadi-sultan/ep063/playlist.m3u8
            const match = sourceUrl.match(/ep(\d+)/);
            const epString = match ? match[0] : `ep${ep.episodeNumber.toString().padStart(3, '0')}`;
            
            const r2Key = `melolo/dari-miskin-jadi-sultan/${epString}_540p.mp4`;
            const localFile = `temp_${epString}_540p.mp4`;
            
            console.log(`[FFMPEG] Mendownload & Konversi ${sourceUrl} ke 540p (faststart)...`);
            
            // Command FFmpeg: 
            // - scale=-2:540 (Resolusi 540p)
            // - preset fast, crf 28 (Kompresi cepat dan ringan)
            // - movflags +faststart (Video bisa langsung dimainkan tanpa nunggu download selesai)
            const cmd = `ffmpeg -y -i "${sourceUrl}" -vf scale=-2:540 -c:v libx264 -preset fast -crf 28 -c:a aac -b:a 128k -movflags +faststart "${localFile}"`;
            
            try {
                execSync(cmd, { stdio: 'inherit' });
                console.log(`[UPLOAD] Mengunggah ${localFile} ke R2 (${r2Key})...`);
                await uploadToR2(localFile, r2Key);
                
                console.log(`[CLEANUP] Menghapus file lokal ${localFile}...`);
                if (fs.existsSync(localFile)) {
                    fs.unlinkSync(localFile);
                }
                
                console.log(`✅ Episode ${ep.episodeNumber} selesai!`);
            } catch (ffmpegErr) {
                console.error(`❌ Gagal memproses episode ${ep.episodeNumber}:`, ffmpegErr.message);
            }
        }
        
        console.log("\n🎉 SEMUA SELESAI!");
        console.log("Untuk memasukkan data 540p ini ke database, jalankan `node backfill_r2_to_db.js` di production/Coolify Anda.");
        
    } catch (err) {
        console.error("Terjadi kesalahan:", err);
    }
}

convertAndUpload();

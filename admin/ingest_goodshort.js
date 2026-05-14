/**
 * Ingestion Script for Goodshort Pipeline
 * Membaca file JSON hasil dari pipeline_goodshort.py dan memasukkannya ke DB dengan isActive: false
 */
const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const p = new PrismaClient();
const JSON_FILE = path.join(__dirname, '../goodshort_ingest_data.json');

async function main() {
    console.log('=== STARTING GOODSHORT DB INGESTION ===\n');

    if (!fs.existsSync(JSON_FILE)) {
        console.error(`[X] File JSON tidak ditemukan: ${JSON_FILE}`);
        console.log('Pastikan Anda sudah menjalankan script Python (pipeline_goodshort.py) terlebih dahulu!');
        process.exit(1);
    }

    const data = JSON.parse(fs.readFileSync(JSON_FILE, 'utf-8'));
    console.log(`Membaca ${data.length} drama dari file JSON...`);

    let registered = 0, skipped = 0, failed = 0;

    for (const d of data) {
        try {
            // Cek apakah drama dengan judul ini sudah ada di DB
            const existing = await p.drama.findFirst({
                where: { title: d.title }
            });

            if (existing) {
                console.log(`[SKIP] Drama sudah ada di DB: ${d.title}`);
                skipped++;
                continue;
            }

            console.log(`[+] Mendaftarkan Drama: ${d.title}`);
            
            // 1. Buat Drama (dengan isActive: false / PENDING)
            const newDrama = await p.drama.create({
                data: {
                    title: d.title,
                    description: d.description || d.title,
                    cover: d.cover,
                    genres: d.genres || ['Drama'],
                    status: 'completed',
                    country: 'China',
                    language: 'Indonesia',
                    isActive: false, // SESUAI PERMINTAAN: Status PENDING / Tidak Aktif
                    views: 0,
                    rating: 0,
                    totalEpisodes: d.totalEpisodes,
                }
            });

            // 2. Buat seluruh Episodenya
            if (d.episodes && d.episodes.length > 0) {
                await p.episode.createMany({
                    data: d.episodes.map(ep => ({
                        dramaId: newDrama.id,
                        episodeNumber: ep.number,
                        title: `Episode ${ep.number}`,
                        videoUrl: ep.url_720p, // Default menggunakan 720p
                        // Jika Prisma schema Anda mendukung field tambahan untuk 540p, bisa ditambahkan di sini.
                        isActive: false, // Set false agar mengikuti status dramanya
                        isVip: false,
                        coinPrice: 0,
                        views: 0,
                        duration: 0,
                    })),
                    skipDuplicates: true,
                });
                console.log(`    -> Berhasil menginjek ${d.episodes.length} Episode.`);
            }

            registered++;

        } catch (e) {
            console.log(`[ERROR] Gagal memasukkan ${d.title}:`, e.message);
            failed++;
        }
    }

    console.log(`\n=== INGESTION SELESAI ===`);
    console.log(`✅ Berhasil: ${registered} Drama`);
    console.log(`⏭️ Di-skip (sudah ada): ${skipped} Drama`);
    console.log(`❌ Gagal: ${failed} Drama`);

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });

/**
 * Export dramas & episodes from local Prisma DB → SQL for VPS Supabase (Drizzle schema)
 * VPS tables: dramas (snake_case), episodes (snake_case)
 */
const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const path = require('path');

const prisma = new PrismaClient();
const OUT = path.join(__dirname, '..', 'cf-backend', 'scripts', 'output', 'sync_vps.sql');

function esc(v) {
    if (v === null || v === undefined) return 'NULL';
    if (typeof v === 'boolean') return v ? 'true' : 'false';
    if (typeof v === 'number') return String(v);
    if (v instanceof Date) return `'${v.toISOString()}'`;
    if (Array.isArray(v)) return `'${JSON.stringify(v).replace(/'/g, "''")}'::jsonb`;
    return `'${String(v).replace(/'/g, "''")}'`;
}

async function main() {
    const dramas = await prisma.drama.findMany({
        include: { episodes: true },
        orderBy: { createdAt: 'asc' },
    });

    console.log(`Exporting ${dramas.length} dramas...`);

    let sql = '-- Auto-generated: Sync local DB to VPS Supabase\n';
    sql += '-- Generated: ' + new Date().toISOString() + '\n\n';

    let dramaCount = 0, epCount = 0;

    for (const d of dramas) {
        const now = new Date().toISOString();
        sql += `INSERT INTO dramas (id, title, description, cover, banner, genres, tag_list, total_episodes, rating, views, likes, review_count, average_rating, status, is_vip, is_featured, is_active, age_rating, release_date, director, "cast", country, language, created_at, updated_at) VALUES (${esc(d.id)}, ${esc(d.title)}, ${esc(d.description)}, ${esc(d.cover)}, ${esc(d.banner)}, ${esc(d.genres)}, ${esc(d.tagList || [])}, ${d.totalEpisodes}, ${d.rating}, ${d.views}, ${d.likes}, ${d.reviewCount || 0}, ${d.averageRating || 0}, ${esc(d.status)}, ${d.isVip}, ${d.isFeatured}, ${d.isActive}, ${esc(d.ageRating || 'all')}, ${d.releaseDate ? esc(d.releaseDate) : 'NULL'}, ${esc(d.director)}, ${esc(d.cast || [])}, ${esc(d.country)}, ${esc(d.language)}, ${esc(d.createdAt)}, ${esc(d.updatedAt)}) ON CONFLICT (id) DO UPDATE SET total_episodes = EXCLUDED.total_episodes, updated_at = NOW();\n`;
        dramaCount++;

        for (const ep of d.episodes) {
            sql += `INSERT INTO episodes (id, drama_id, episode_number, title, description, thumbnail, video_url, duration, is_vip, coin_price, views, is_active, release_date, created_at, updated_at) VALUES (${esc(ep.id)}, ${esc(ep.dramaId)}, ${ep.episodeNumber}, ${esc(ep.title)}, ${esc(ep.description)}, ${esc(ep.thumbnail)}, ${esc(ep.videoUrl)}, ${ep.duration}, ${ep.isVip}, ${ep.coinPrice}, ${ep.views}, ${ep.isActive}, ${esc(ep.releaseDate || ep.createdAt)}, ${esc(ep.createdAt)}, ${esc(ep.updatedAt)}) ON CONFLICT (drama_id, episode_number) DO UPDATE SET video_url = EXCLUDED.video_url, updated_at = NOW();\n`;
            epCount++;
        }
        sql += '\n';
    }

    // Also export users
    const users = await prisma.user.findMany({ orderBy: { createdAt: 'asc' } });
    sql += '\n-- Users\n';
    for (const u of users) {
        sql += `INSERT INTO users (id, email, password, name, avatar, provider, provider_id, role, is_guest, guest_id, coins, vip_status, is_active, created_at, updated_at) VALUES (${esc(u.id)}, ${esc(u.email)}, ${esc(u.password)}, ${esc(u.name)}, ${esc(u.avatar)}, ${esc(u.provider)}, ${esc(u.providerId)}, ${esc(u.role)}, ${u.isGuest}, ${esc(u.guestId)}, ${u.coins}, ${u.vipStatus}, ${u.isActive}, ${esc(u.createdAt)}, ${esc(u.updatedAt)}) ON CONFLICT (id) DO NOTHING;\n`;
    }

    fs.writeFileSync(OUT, sql);
    console.log(`\nExported to: ${OUT}`);
    console.log(`  Dramas: ${dramaCount}`);
    console.log(`  Episodes: ${epCount}`);
    console.log(`  Users: ${users.length}`);
    console.log(`  File size: ${(fs.statSync(OUT).size / 1024 / 1024).toFixed(1)} MB`);

    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });

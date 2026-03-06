/**
 * Data Migration Script: Local PostgreSQL → D1 via wrangler CLI
 * 
 * Usage:
 *   npx tsx scripts/migrate-data.ts
 * 
 * This script:
 * 1. Connects to local PostgreSQL  
 * 2. Exports data as INSERT SQL statements
 * 3. Writes SQL files
 * 4. Then you apply them via: npx wrangler d1 execute kingshortid --remote --file=scripts/output/dramas.sql
 */

import pg from 'pg';
import fs from 'fs';
import path from 'path';

const { Client } = pg;

const DB_URL = process.env.DATABASE_URL || 'postgresql://postgres:seiman21@localhost:5432/kingshort?schema=public';
const OUTPUT_DIR = path.join(process.cwd(), 'scripts', 'output');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// Escape string for SQLite
function esc(val: any): string {
    if (val === null || val === undefined) return 'NULL';
    if (typeof val === 'boolean') return val ? '1' : '0';
    if (typeof val === 'number') return String(val);
    if (val instanceof Date) return String(Math.floor(val.getTime() / 1000));
    if (Array.isArray(val)) return `'${JSON.stringify(val).replace(/'/g, "''")}'`;
    const str = String(val).replace(/'/g, "''");
    return `'${str}'`;
}

function toTs(date: any): string {
    if (!date) return 'NULL';
    const d = new Date(date);
    return isNaN(d.getTime()) ? 'NULL' : String(Math.floor(d.getTime() / 1000));
}

function toJson(arr: any): string {
    if (!arr) return `'[]'`;
    if (Array.isArray(arr)) return `'${JSON.stringify(arr).replace(/'/g, "''")}'`;
    return `'[]'`;
}

async function main() {
    console.log('🚀 KingShortID Data Migration: PostgreSQL → SQL files for D1\n');

    const client = new Client({ connectionString: DB_URL });
    await client.connect();
    console.log('✅ Connected to PostgreSQL\n');

    // ==================== DRAMAS ====================
    console.log('🎬 Exporting Dramas...');
    const dramas = await client.query('SELECT * FROM "Drama" WHERE "isActive" = true ORDER BY "createdAt" ASC');
    const dramasSql: string[] = [];

    for (const d of dramas.rows) {
        dramasSql.push(
            `INSERT OR IGNORE INTO dramas (id, title, description, cover, banner, genres, tag_list, ` +
            `total_episodes, rating, views, likes, review_count, average_rating, ` +
            `status, is_vip, is_featured, is_active, age_rating, ` +
            `release_date, director, cast, country, language, created_at, updated_at) VALUES (` +
            `${esc(d.id)}, ${esc(d.title)}, ${esc(d.description || '')}, ${esc(d.cover || '')}, ${esc(d.banner)}, ` +
            `${toJson(d.genres)}, ${toJson(d.tagList)}, ` +
            `${d.totalEpisodes || 0}, ${d.rating || 0}, ${d.views || 0}, ${d.likes || 0}, ` +
            `${d.reviewCount || 0}, ${d.averageRating || 0}, ` +
            `${esc(d.status || 'ongoing')}, ${d.isVip ? 1 : 0}, ${d.isFeatured ? 1 : 0}, 1, ${esc(d.ageRating || 'all')}, ` +
            `${toTs(d.releaseDate)}, ${esc(d.director)}, ${toJson(d.cast)}, ` +
            `${esc(d.country || 'China')}, ${esc(d.language || 'Indonesia')}, ` +
            `${toTs(d.createdAt)}, ${toTs(d.updatedAt)});`
        );
    }
    fs.writeFileSync(path.join(OUTPUT_DIR, 'dramas.sql'), dramasSql.join('\n'), 'utf8');
    console.log(`  ✅ ${dramas.rows.length} dramas → dramas.sql\n`);

    // ==================== EPISODES ====================
    console.log('📺 Exporting Episodes...');
    const episodes = await client.query('SELECT * FROM "Episode" WHERE "isActive" = true ORDER BY "dramaId", "episodeNumber" ASC');

    // Split into chunks of 500 for large files
    const CHUNK_SIZE = 500;
    const totalChunks = Math.ceil(episodes.rows.length / CHUNK_SIZE);

    for (let chunk = 0; chunk < totalChunks; chunk++) {
        const start = chunk * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, episodes.rows.length);
        const epSql: string[] = [];

        for (let i = start; i < end; i++) {
            const e = episodes.rows[i];
            epSql.push(
                `INSERT OR IGNORE INTO episodes (id, drama_id, episode_number, title, description, thumbnail, ` +
                `video_url, duration, is_vip, coin_price, views, is_active, ` +
                `release_date, created_at, updated_at, season_id) VALUES (` +
                `${esc(e.id)}, ${esc(e.dramaId)}, ${e.episodeNumber}, ${esc(e.title || `Episode ${e.episodeNumber}`)}, ` +
                `${esc(e.description)}, ${esc(e.thumbnail)}, ` +
                `${esc(e.videoUrl)}, ${e.duration || 0}, ${e.isVip ? 1 : 0}, ${e.coinPrice || 0}, ` +
                `${e.views || 0}, 1, ` +
                `${toTs(e.releaseDate || e.createdAt)}, ${toTs(e.createdAt)}, ${toTs(e.updatedAt)}, ${esc(e.seasonId)});`
            );
        }

        const filename = `episodes_${String(chunk + 1).padStart(2, '0')}.sql`;
        fs.writeFileSync(path.join(OUTPUT_DIR, filename), epSql.join('\n'), 'utf8');
        console.log(`  → ${filename}: ${epSql.length} episodes`);
    }
    console.log(`  ✅ ${episodes.rows.length} episodes total → ${totalChunks} files\n`);

    // ==================== USERS ====================
    console.log('👤 Exporting Users...');
    const users = await client.query('SELECT * FROM "User" ORDER BY "createdAt" ASC');
    const usersSql: string[] = [];

    for (const u of users.rows) {
        usersSql.push(
            `INSERT OR IGNORE INTO users (id, email, password, name, avatar, provider, provider_id, role, ` +
            `is_guest, guest_id, coins, vip_status, vip_expiry, ` +
            `last_check_in, check_in_streak, last_spin_date, total_spins, ` +
            `preferences, total_watch_time, follower_count, following_count, bio, ` +
            `push_token, notify_episodes, notify_coins, notify_system, ` +
            `is_active, created_at, updated_at) VALUES (` +
            `${esc(u.id)}, ${esc(u.email)}, ${esc(u.password)}, ${esc(u.name)}, ${esc(u.avatar)}, ` +
            `${esc(u.provider || 'local')}, ${esc(u.providerId)}, ${esc(u.role || 'user')}, ` +
            `${u.isGuest ? 1 : 0}, ${esc(u.guestId)}, ${u.coins || 0}, ` +
            `${u.vipStatus ? 1 : 0}, ${toTs(u.vipExpiry)}, ` +
            `${toTs(u.lastCheckIn)}, ${u.checkInStreak || 0}, ${toTs(u.lastSpinDate)}, ${u.totalSpins || 0}, ` +
            `${u.preferences ? esc(JSON.stringify(u.preferences)) : 'NULL'}, ` +
            `${u.totalWatchTime || 0}, ${u.followerCount || 0}, ${u.followingCount || 0}, ${esc(u.bio)}, ` +
            `${esc(u.pushToken)}, ${u.notifyEpisodes !== false ? 1 : 0}, ` +
            `${u.notifyCoins !== false ? 1 : 0}, ${u.notifySystem !== false ? 1 : 0}, ` +
            `1, ${toTs(u.createdAt)}, ${toTs(u.updatedAt)});`
        );
    }
    fs.writeFileSync(path.join(OUTPUT_DIR, 'users.sql'), usersSql.join('\n'), 'utf8');
    console.log(`  ✅ ${users.rows.length} users → users.sql\n`);

    // ==================== CATEGORIES ====================
    console.log('📂 Exporting Categories...');
    try {
        const categories = await client.query('SELECT * FROM "Category" ORDER BY "order" ASC');
        const catSql: string[] = [];
        for (const c of categories.rows) {
            catSql.push(
                `INSERT OR IGNORE INTO categories (id, name, slug, icon, "order") VALUES (` +
                `${esc(c.id)}, ${esc(c.name)}, ${esc(c.slug)}, ${esc(c.icon)}, ${c.order || 0});`
            );
        }
        fs.writeFileSync(path.join(OUTPUT_DIR, 'categories.sql'), catSql.join('\n'), 'utf8');
        console.log(`  ✅ ${categories.rows.length} categories → categories.sql\n`);
    } catch {
        console.log('  ⏭️  No Category table, skipping\n');
    }

    // ==================== SUBTITLES ====================
    console.log('💬 Exporting Subtitles...');
    try {
        const subtitles = await client.query('SELECT * FROM "Subtitle" ORDER BY "episodeId" ASC');
        if (subtitles.rows.length > 0) {
            const subSql: string[] = [];
            for (const s of subtitles.rows) {
                subSql.push(
                    `INSERT OR IGNORE INTO subtitles (id, episode_id, language, label, url, is_default, created_at) VALUES (` +
                    `${esc(s.id)}, ${esc(s.episodeId)}, ${esc(s.language)}, ${esc(s.label)}, ${esc(s.url)}, ` +
                    `${s.isDefault ? 1 : 0}, ${toTs(s.createdAt)});`
                );
            }
            fs.writeFileSync(path.join(OUTPUT_DIR, 'subtitles.sql'), subSql.join('\n'), 'utf8');
            console.log(`  ✅ ${subtitles.rows.length} subtitles → subtitles.sql\n`);
        } else {
            console.log('  ⏭️  0 subtitles\n');
        }
    } catch {
        console.log('  ⏭️  No Subtitle table, skipping\n');
    }

    await client.end();

    console.log('═══════════════════════════════════════════════════');
    console.log('✅ SQL files generated in scripts/output/');
    console.log('═══════════════════════════════════════════════════');
    console.log('\nTo import to D1, run these commands:');
    console.log('  npx wrangler d1 execute kingshortid --remote --file=scripts/output/categories.sql');
    console.log('  npx wrangler d1 execute kingshortid --remote --file=scripts/output/dramas.sql');

    // List episode files
    const epFiles = fs.readdirSync(OUTPUT_DIR).filter(f => f.startsWith('episodes_')).sort();
    for (const f of epFiles) {
        console.log(`  npx wrangler d1 execute kingshortid --remote --file=scripts/output/${f}`);
    }
    console.log('  npx wrangler d1 execute kingshortid --remote --file=scripts/output/users.sql');
}

main().catch(console.error);

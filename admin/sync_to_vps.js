/**
 * Sync local Prisma DB → VPS Supabase via REST API (PostgREST)
 */
const { PrismaClient } = require('@prisma/client');
require('dotenv').config({ path: require('path').join(__dirname, '..', 'cf-backend', '.env') });

const prisma = new PrismaClient();

const SUPABASE_URL = process.env.SUPABASE_URL || 'http://141.11.160.187:8000';
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY;

if (!SUPABASE_KEY) {
    console.error('Missing SUPABASE_SERVICE_KEY in cf-backend/.env');
    process.exit(1);
}

async function supabaseUpsert(table, rows, onConflict = 'id') {
    const BATCH = 100;
    let total = 0;
    for (let i = 0; i < rows.length; i += BATCH) {
        const batch = rows.slice(i, i + BATCH);
        const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`,
                'Prefer': `resolution=merge-duplicates`,
            },
            body: JSON.stringify(batch),
        });
        if (!res.ok) {
            const err = await res.text();
            console.error(`  Error batch ${i}: ${err.slice(0, 200)}`);
        } else {
            total += batch.length;
        }
        if ((i + BATCH) % 500 === 0 || i + BATCH >= rows.length) {
            console.log(`  ... ${Math.min(i + BATCH, rows.length)}/${rows.length}`);
        }
    }
    return total;
}

async function main() {
    console.log(`Supabase URL: ${SUPABASE_URL}`);
    console.log(`Service Key: ${SUPABASE_KEY?.slice(0, 20)}...\n`);

    // 1. Sync Users
    console.log('=== Syncing Users ===');
    const users = await prisma.user.findMany({ orderBy: { createdAt: 'asc' } });
    const userRows = users.map(u => ({
        id: u.id, email: u.email, password: u.password, name: u.name,
        avatar: u.avatar, provider: u.provider, provider_id: u.providerId,
        role: u.role, is_guest: u.isGuest, guest_id: u.guestId,
        coins: u.coins, vip_status: u.vipStatus, is_active: u.isActive,
        created_at: u.createdAt?.toISOString(), updated_at: (u.updatedAt || new Date()).toISOString(),
    }));
    const userCount = await supabaseUpsert('users', userRows);
    console.log(`  Users: ${userCount}\n`);

    // 2. Sync Dramas
    console.log('=== Syncing Dramas ===');
    const dramas = await prisma.drama.findMany({ orderBy: { createdAt: 'asc' } });
    const dramaRows = dramas.map(d => ({
        id: d.id, title: d.title, description: d.description, cover: d.cover,
        banner: d.banner, genres: d.genres || [], tag_list: d.tagList || [],
        total_episodes: d.totalEpisodes, rating: d.rating, views: d.views, likes: d.likes,
        review_count: d.reviewCount || 0, average_rating: d.averageRating || 0,
        status: d.status, is_vip: d.isVip, is_featured: d.isFeatured, is_active: d.isActive,
        age_rating: d.ageRating || 'all', release_date: d.releaseDate?.toISOString() || null,
        director: d.director, cast: d.cast || [], country: d.country, language: d.language,
        created_at: d.createdAt?.toISOString(), updated_at: (d.updatedAt || new Date()).toISOString(),
    }));
    const dramaCount = await supabaseUpsert('dramas', dramaRows);
    console.log(`  Dramas: ${dramaCount}\n`);

    // 3. Sync Episodes
    console.log('=== Syncing Episodes ===');
    const episodes = await prisma.episode.findMany({ orderBy: { createdAt: 'asc' } });
    const epRows = episodes.map(ep => ({
        id: ep.id, drama_id: ep.dramaId, episode_number: ep.episodeNumber,
        title: ep.title, description: ep.description, thumbnail: ep.thumbnail,
        video_url: ep.videoUrl, duration: ep.duration, is_vip: ep.isVip,
        coin_price: ep.coinPrice, views: ep.views, is_active: ep.isActive,
        release_date: (ep.releaseDate || ep.createdAt)?.toISOString(),
        created_at: ep.createdAt?.toISOString(), updated_at: (ep.updatedAt || new Date()).toISOString(),
    }));
    const epCount = await supabaseUpsert('episodes', epRows);
    console.log(`  Episodes: ${epCount}\n`);

    // 4. Sync Subtitles
    console.log('=== Syncing Subtitles ===');
    const subs = await prisma.subtitle.findMany();
    if (subs.length > 0) {
        const subRows = subs.map(s => ({
            id: s.id, episode_id: s.episodeId, language: s.language,
            label: s.label, url: s.url, is_default: s.isDefault,
            created_at: s.createdAt?.toISOString(),
        }));
        const subCount = await supabaseUpsert('subtitles', subRows);
        console.log(`  Subtitles: ${subCount}\n`);
    } else {
        console.log('  No subtitles to sync\n');
    }

    console.log('=== DONE ===');
    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });

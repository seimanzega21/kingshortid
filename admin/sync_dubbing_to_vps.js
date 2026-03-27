/**
 * Sync dubbing dramas to VPS v2
 * Strategy: 
 *   - Get existing VPS drama list first (they were synced before with basic data)
 *   - PATCH each drama with cover, genres, tagList (bypasses URL validation)
 *   - POST episodes (R2 URLs pass validation)
 *   - Rate-limit friendly with delays
 */
const { PrismaClient } = require('@prisma/client');
require('dotenv').config();

const prisma = new PrismaClient();
const VPS = 'https://api.shortlovers.id';
const API_KEY = process.env.ADMIN_API_KEY || 'ksh-admin-2026-s3cur3-k3y-x7m9p2';

async function vps(method, path, body) {
    const res = await fetch(`${VPS}${path}`, {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': API_KEY,
        },
        body: body ? JSON.stringify(body) : undefined,
    });
    const text = await res.text();
    try { return { ok: res.ok, status: res.status, data: JSON.parse(text) }; }
    catch { return { ok: res.ok, status: res.status, data: text }; }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
    console.log('═'.repeat(60));
    console.log('  Sync Dubbing Dramas → VPS (v2 - PATCH approach)');
    console.log('═'.repeat(60));

    // 1. Get all dramas from VPS to find existing IDs
    console.log('\n[1/3] Fetching VPS drama list...');
    const vpsRes = await vps('GET', '/api/dramas?includeInactive=true&limit=9999');
    if (!vpsRes.ok) {
        console.error('Failed to get VPS dramas:', vpsRes.data);
        process.exit(1);
    }
    const vpsDramas = vpsRes.data.dramas || [];
    console.log(`  VPS has ${vpsDramas.length} dramas total`);
    
    // Build title → VPS ID lookup
    const vpsByTitle = {};
    for (const d of vpsDramas) {
        vpsByTitle[d.title.toLowerCase().trim()] = d;
    }

    // 2. Get local dubbing dramas with episodes
    console.log('\n[2/3] Loading local dubbing dramas...');
    const localDramas = await prisma.drama.findMany({
        where: {
            OR: [
                { description: { contains: '[FRkey:' } },
                { tagList: { has: 'Dubbing' } },
                { description: { contains: 'Sulih Suara' } },
            ],
        },
        include: {
            episodes: { orderBy: { episodeNumber: 'asc' } },
        },
        orderBy: { title: 'asc' },
    });
    console.log(`  Found ${localDramas.length} local dubbing dramas`);

    // 3. Sync via PATCH (drama) + POST (episodes)
    console.log('\n[3/3] Syncing...\n');
    let patchOk = 0, patchFail = 0, epOk = 0, epFail = 0, epSkip = 0;

    for (const d of localDramas) {
        const vpsMatch = vpsByTitle[d.title.toLowerCase().trim()];
        
        if (!vpsMatch) {
            console.log(`  ⊘ ${d.title.substring(0, 50)} — NOT on VPS, skipping`);
            continue;
        }

        const vpsId = vpsMatch.id;

        // PATCH drama with cover, genres, tagList
        const patchData = {};
        if (d.cover && d.cover.startsWith('http') && (!vpsMatch.cover || vpsMatch.cover.length < 5)) {
            patchData.cover = d.cover;
        }
        if (d.genres && d.genres.length > 0) {
            patchData.genres = d.genres;
        }
        patchData.tagList = d.tagList && d.tagList.length > 0 ? d.tagList : ['Dubbing'];
        patchData.banner = d.banner || d.cover || '';
        patchData.country = d.country || 'China';
        patchData.language = d.language || 'Indonesia';

        const pRes = await vps('PATCH', `/api/dramas/${vpsId}`, patchData);
        if (pRes.ok) {
            patchOk++;
        } else {
            console.log(`  ✗ PATCH ${d.title.substring(0, 40)}: ${pRes.status} ${JSON.stringify(pRes.data).substring(0, 80)}`);
            patchFail++;
        }

        // POST episodes (always try)
        let epsAdded = 0;
        
        if (d.episodes.length > 0) {
            for (const ep of d.episodes) {
                if (!ep.videoUrl) { epSkip++; continue; }

                const epRes = await vps('POST', '/api/episodes', {
                    dramaId: vpsId,
                    episodeNumber: ep.episodeNumber,
                    title: ep.title || `Episode ${ep.episodeNumber}`,
                    videoUrl: ep.videoUrl,
                    duration: ep.duration || 0,
                });

                if (epRes.ok) {
                    epOk++;
                    epsAdded++;
                } else if (epRes.status === 429) {
                    // Rate limited — wait and retry
                    console.log(`  ⏳ Rate limited, waiting 5s...`);
                    await sleep(5000);
                    const retry = await vps('POST', '/api/episodes', {
                        dramaId: vpsId,
                        episodeNumber: ep.episodeNumber,
                        title: ep.title || `Episode ${ep.episodeNumber}`,
                        videoUrl: ep.videoUrl,
                        duration: ep.duration || 0,
                    });
                    if (retry.ok) { epOk++; epsAdded++; }
                    else { epFail++; }
                } else {
                    epFail++;
                    if (epRes.status !== 400) { // Skip logging for already-existing episodes
                        console.log(`    ep${ep.episodeNumber}: ${epRes.status} ${JSON.stringify(epRes.data).substring(0, 60)}`);
                    }
                }

                // Small delay between requests
                await sleep(250);
            }
        }

        const coverStatus = patchData.cover ? '🖼️' : '  ';
        console.log(`  ✓ ${coverStatus} ${d.title.substring(0, 45).padEnd(45)} vps=${vpsId.substring(0, 8)} +${epsAdded}/${d.episodes.length} eps`);
        
        // Delay between dramas
        await sleep(500);
    }

    console.log(`\n${'═'.repeat(60)}`);
    console.log(`  ✓ Dramas patched:  ${patchOk} (failed: ${patchFail})`);
    console.log(`  📺 Episodes added:  ${epOk} (failed: ${epFail}, skipped: ${epSkip})`);
    console.log('═'.repeat(60));

    await prisma.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });

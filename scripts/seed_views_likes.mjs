/**
 * Seed natural views & likes for all dramas
 * Formula: views based on totalEpisodes, likes = 5-12% of views
 * Includes delay to avoid 429 rate limiting
 */
const API = 'https://kingshortid-api.toonplay-seiman.workers.dev/api';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function seed() {
    // Fetch all dramas
    const res = await fetch(`${API}/dramas?limit=9999`);
    const data = await res.json();
    const dramas = data.dramas || data;

    // Only seed dramas that still have 0 likes (skip already seeded)
    const toSeed = dramas.filter(d => !d.likes || d.likes === 0);
    console.log(`Found ${dramas.length} total dramas, ${toSeed.length} need seeding\n`);

    let updated = 0;
    for (let i = 0; i < toSeed.length; i++) {
        const drama = toSeed[i];
        const eps = drama.totalEpisodes || 1;

        // Views: base 500-1500 + 50-100 per episode
        const baseViews = 500 + Math.floor(Math.random() * 1000);
        const epBonus = eps * (50 + Math.floor(Math.random() * 50));
        const views = baseViews + epBonus;

        // Likes: 5-12% of views
        const likePercent = 0.05 + Math.random() * 0.07;
        const likes = Math.floor(views * likePercent);

        try {
            const patchRes = await fetch(`${API}/dramas/${drama.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ views, likes }),
            });

            if (patchRes.ok) {
                updated++;
                console.log(`[${i + 1}/${toSeed.length}] ✅ ${drama.title} → views: ${views.toLocaleString()}, likes: ${likes.toLocaleString()}`);
            } else if (patchRes.status === 429) {
                console.log(`[${i + 1}] ⏳ Rate limited, waiting 2s...`);
                await sleep(2000);
                i--; // retry
                continue;
            } else {
                console.log(`[${i + 1}] ❌ ${drama.title} → ${patchRes.status}`);
            }
        } catch (e) {
            console.log(`[${i + 1}] ❌ ${drama.title} → ${e.message}`);
        }

        // Delay 200ms between requests to avoid rate limiting
        await sleep(200);
    }

    console.log(`\n🎉 Seeded ${updated}/${toSeed.length} remaining dramas`);
}

seed();

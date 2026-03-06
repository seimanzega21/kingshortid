/**
 * Find all dramas with broken cover URLs and fix .jpg → .webp
 */
const API = 'https://kingshortid-api.toonplay-seiman.workers.dev/api';

// Fetch all dramas
const res = await fetch(`${API}/dramas?limit=9999&includeInactive=true`);
const data = await res.json();
const allDramas = data.dramas;
console.log(`Total dramas: ${allDramas.length}`);

const broken = [];
const batchSize = 10;

for (let i = 0; i < allDramas.length; i += batchSize) {
    const batch = allDramas.slice(i, i + batchSize);
    const results = await Promise.all(batch.map(async d => {
        if (!d.cover) return { id: d.id, title: d.title, cover: null, status: 'NO_COVER' };
        try {
            const r = await fetch(d.cover, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
            if (r.status !== 200) {
                return { id: d.id, title: d.title, cover: d.cover, status: r.status };
            }
            return null; // OK
        } catch (e) {
            return { id: d.id, title: d.title, cover: d.cover, status: 'ERR' };
        }
    }));
    broken.push(...results.filter(Boolean));
    process.stdout.write(`\r  Checked ${Math.min(i + batchSize, allDramas.length)}/${allDramas.length}...`);
}

console.log(`\n\nBroken covers: ${broken.length}`);

// Check if .webp versions exist for broken ones
const fixable = [];
for (const b of broken) {
    if (!b.cover || !b.cover.endsWith('.jpg')) continue;
    const webpUrl = b.cover.replace(/\.jpg$/, '.webp');
    try {
        const r = await fetch(webpUrl, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
        if (r.status === 200) {
            fixable.push({ ...b, webpUrl });
        }
    } catch { }
}

console.log(`Fixable (.jpg → .webp): ${fixable.length}`);
fixable.forEach(f => console.log(`  ${f.title}`));

// Write results
const fs = await import('fs');
fs.writeFileSync('broken_covers.json', JSON.stringify({ broken, fixable }, null, 2));
console.log('\nSaved to broken_covers.json');

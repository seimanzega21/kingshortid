const fs = require('fs');
async function main() {
    const r = await fetch('https://kingshortid-api.toonplay-seiman.workers.dev/api/dramas?limit=300');
    const d = await r.json();
    const list = Array.isArray(d) ? d : d.dramas || [];

    const broken = [];
    for (const x of list) {
        try {
            const h = await fetch(x.cover, { method: 'HEAD' });
            if (h.status !== 200) {
                const slug = x.cover.split('/melolo/')[1]?.split('/')[0] || '?';
                broken.push({ title: x.title, id: x.id, cover: x.cover, slug, status: h.status });
            }
        } catch (e) {
            broken.push({ title: x.title, id: x.id, cover: x.cover, slug: '?', status: 'ERR' });
        }
    }

    const report = broken.map((b, i) => `[${i + 1}] ${b.title}\n    ID: ${b.id}\n    Slug: ${b.slug}\n    Cover: ${b.cover}\n    Status: ${b.status}`).join('\n\n');

    const out = `BROKEN COVERS: ${broken.length}\n\n${report}`;
    fs.writeFileSync('d:/kingshortid/scripts/broken_covers.txt', out);
    console.log('Written to broken_covers.txt');
}
main();

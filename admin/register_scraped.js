const { PrismaClient } = require('@prisma/client');
const https = require('https');
const p = new PrismaClient();

const R2_PUBLIC = 'https://stream.shortlovers.id';

function fetchJSON(url) {
    return new Promise((resolve, reject) => {
        https.get(url, { timeout: 15000 }, res => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch (e) { reject(e); }
            });
        }).on('error', reject);
    });
}

async function main() {
    const dramas = [
        { search: 'Romansa Setelah', slug: 'romansa-setelah-pernikahan', epsOnR2: 26 },
        { search: 'Dimanja Habis', slug: 'dimanja-habis-habisan-oleh-bos', epsOnR2: 38 },
    ];

    for (const d of dramas) {
        process.stdout.write('\n=== ' + d.slug + ' ===\n');

        // Check if exists
        const existing = await p.drama.findFirst({ where: { title: { contains: d.search } } });
        if (existing) {
            process.stdout.write('  Already exists: ' + existing.id + '\n');
            continue;
        }

        // Search Vidrama
        process.stdout.write('  Searching Vidrama...\n');
        const searchData = await fetchJSON(
            'https://vidrama.asia/api/melolo?action=search&keyword=' + encodeURIComponent(d.search) + '&limit=10'
        );
        const items = searchData.data || [];
        const match = items.find(x => x.title.toLowerCase().includes(d.search.toLowerCase()));
        if (!match) {
            process.stdout.write('  NOT FOUND on Vidrama!\n');
            continue;
        }

        // Get detail
        const detailData = await fetchJSON(
            'https://vidrama.asia/api/melolo?action=detail&id=' + match.id
        );
        const detail = detailData.data || {};

        const title = match.title;
        const desc = detail.description || detail.desc || match.description || 'Drama series dari Melolo';
        const genres = detail.genres || match.genres || [];
        const totalEps = (detail.episodes || []).length;
        const coverUrl = R2_PUBLIC + '/melolo/' + d.slug + '/cover.jpg';

        process.stdout.write('  Title: ' + title + '\n');
        process.stdout.write('  Desc: ' + desc.substring(0, 80) + '...\n');
        process.stdout.write('  Genres: ' + JSON.stringify(genres) + '\n');
        process.stdout.write('  Total eps: ' + totalEps + '\n');
        process.stdout.write('  Cover: ' + coverUrl + '\n');

        // Create drama
        const drama = await p.drama.create({
            data: {
                title: title,
                description: desc,
                cover: coverUrl,
                genres: Array.isArray(genres) ? genres : [],
                totalEpisodes: totalEps,
                rating: 4.5,
                views: Math.floor(Math.random() * 5000) + 1000,
                status: 'ongoing',
                isActive: true,
                country: 'China',
                language: 'Mandarin',
            }
        });
        process.stdout.write('  Created: ' + drama.id + '\n');

        // Register episodes
        let ok = 0;
        for (let i = 1; i <= d.epsOnR2; i++) {
            await p.episode.create({
                data: {
                    dramaId: drama.id,
                    episodeNumber: i,
                    title: 'Episode ' + i,
                    videoUrl: R2_PUBLIC + '/melolo/' + d.slug + '/ep' + String(i).padStart(3, '0') + '.mp4',
                    duration: 0,
                    isActive: true,
                }
            });
            ok++;
        }
        process.stdout.write('  Registered ' + ok + ' episodes\n');
    }

    // Verify covers
    process.stdout.write('\n=== VERIFY COVERS ===\n');
    for (const d of dramas) {
        const url = R2_PUBLIC + '/melolo/' + d.slug + '/cover.jpg';
        const status = await new Promise(resolve => {
            https.request(url, { method: 'HEAD', timeout: 5000 }, res => resolve(res.statusCode))
                .on('error', () => resolve('ERR')).end();
        });
        process.stdout.write('  ' + d.slug + ': ' + status + '\n');
    }

    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });

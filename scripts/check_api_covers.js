const https = require('https');

const titles = [
    'Pengantin Sang Raja Serigala',
    'Gairah Terlarang',
    'Isi Hatiku Bocor Ibu Menang Telak',
    'Bangkitnya Penguasa Sakti',
    'Ayah, Identitasmu Terungkap!',
    'Menaklukkan Paman Shawn',
    'Aku Bercinta dengan Bos Mafia'
];

async function searchDrama(t) {
    const url = `https://api.shortlovers.id/api/dramas/search?q=${encodeURIComponent(t)}`;
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    resolve(json.dramas || []);
                } catch (e) {
                    resolve([]);
                }
            });
        }).on('error', reject);
    });
}

async function checkUrl(url) {
    return new Promise((resolve) => {
        if (!url) return resolve({ status: 'NULL' });
        const u = new URL(url);
        const req = https.request({
            method: 'HEAD',
            host: u.host,
            path: u.pathname + u.search,
            timeout: 5000
        }, (res) => {
            resolve({ status: res.statusCode, contentType: res.headers['content-type'], location: res.headers['location'] });
        });
        req.on('error', (e) => resolve({ status: 'ERR', error: e.message }));
        req.on('timeout', () => { req.destroy(); resolve({ status: 'TIMEOUT' }); });
        req.end();
    });
}

async function main() {
    for (const t of titles) {
        const dramas = await searchDrama(t);
        const d = dramas.find(x => x.title.toLowerCase().includes(t.toLowerCase()) || t.toLowerCase().includes(x.title.toLowerCase()));
        if (d) {
            const check = await checkUrl(d.cover);
            console.log(`Title: ${d.title}`);
            console.log(`  Cover: ${d.cover}`);
            console.log(`  Status: ${check.status} | Content-Type: ${check.contentType || 'N/A'}`);
            console.log('');
        } else {
            console.log(`NOT FOUND in search: ${t}`);
        }
    }
}

main().catch(console.error);

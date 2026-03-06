
const R2_PUBLIC_BASE = 'https://stream.shortlovers.id';

const PATHS_TO_CHECK = [
    // Check specific segment causing stall (approx 50s mark)
    'si_kembar_lima_bantu_ayah_kejar_ibu/si_kembar_lima_bantu_ayah_kejar_ibu_ep_1/shortlovers_000005.ts'
];

async function checkUrl(path: string) {
    const url = `${R2_PUBLIC_BASE}/${path}`;
    console.log(`\n🔍 Checking: ${url}`);

    try {
        const start = Date.now();
        const res = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Referer': 'https://kingshort.app/',
                'Origin': 'https://kingshort.app'
            }
        });
        const duration = Date.now() - start;

        console.log(`   Status: ${res.status} ${res.statusText}`);
        console.log(`   Time: ${duration}ms`);
        console.log(`   Content-Type: ${res.headers.get('content-type')}`);
        console.log(`   CORS: ${res.headers.get('access-control-allow-origin')}`);

        if (res.ok) {
            console.log('   ✅ SUCCESS');
        } else {
            console.log('   ❌ FAILED');
        }
        return res.ok;
    } catch (error: any) {
        console.error(`   ❌ Error: ${error.message}`);
        return false;
    }
}

async function main() {
    console.log('📡 R2 Custom Domain Diagnostic');
    console.log('==============================');
    console.log(`Domain: ${R2_PUBLIC_BASE}`);

    for (const path of PATHS_TO_CHECK) {
        await checkUrl(path);
    }
}

main().catch(console.error);

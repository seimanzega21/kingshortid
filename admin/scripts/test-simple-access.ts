
const URL = 'https://stream.shortlovers.id/si_kembar_lima_bantu_ayah_kejar_ibu/si_kembar_lima_bantu_ayah_kejar_ibu_ep_1/shortlovers_000005.ts';

async function check() {
    console.log(`Checking plain access: ${URL}`);
    try {
        // Fetch WITHOUT adding any custom headers (Origin, Referer, etc.)
        // This simulates a "dumb" native player request for a segment
        const res = await fetch(URL);

        console.log(`Status: ${res.status}`);
        console.log(`CORS Header: ${res.headers.get('access-control-allow-origin') || 'NULL'}`);
        // console.log(`Content-Type: ${res.headers.get('content-type')}`);

        if (!res.ok) {
            console.log('❌ Request FAILED without headers');
        } else {
            console.log('✅ Request SUCCEEDED (Content Reachable)');
            if (!res.headers.get('access-control-allow-origin')) {
                console.log('⚠️ WARNING: No CORS header returned (Native player might block)');
            }
        }
    } catch (e: any) {
        console.error('Error:', e.message);
    }
}

check();


const BASE_URL = 'https://stream.shortlovers.id/si_kembar_lima_bantu_ayah_kejar_ibu/si_kembar_lima_bantu_ayah_kejar_ibu_ep_1';

async function checkSizes() {
    console.log('📊 Checking Segment Sizes for: Si Kembar Lima...');

    for (let i = 0; i < 10; i++) {
        // Pad with leading zeros (e.g., 000005)
        const num = i.toString().padStart(6, '0');
        const file = `shortlovers_${num}.ts`;
        const url = `${BASE_URL}/${file}`;

        try {
            const start = Date.now();
            const res = await fetch(url, { method: 'HEAD' });
            const size = res.headers.get('content-length');
            const type = res.headers.get('content-type');

            const sizeMB = size ? (parseInt(size) / 1024 / 1024).toFixed(2) : '0';

            console.log(`[${num}] Size: ${sizeMB} MB | Type: ${type} | Status: ${res.status}`);
        } catch (e: any) {
            console.log(`[${num}] ERROR: ${e.message}`);
        }
    }
}

checkSizes();

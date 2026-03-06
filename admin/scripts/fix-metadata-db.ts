import 'dotenv/config';
import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';

const p = new PrismaClient();

async function main() {
    // Read API response to get the real description
    const apiData = JSON.parse(fs.readFileSync('d:/kingshortid/scripts/melolo-scraper/debug_response.json', 'utf-8'));

    // Find series_intro in the response
    function findField(obj: any, key: string, depth = 0): string {
        if (depth > 10) return '';
        if (typeof obj === 'object' && obj !== null) {
            if (key in obj && typeof obj[key] === 'string' && obj[key].length > 10) {
                return obj[key];
            }
            for (const v of Object.values(obj)) {
                const r = findField(v, key, depth + 1);
                if (r) return r;
            }
        }
        if (Array.isArray(obj)) {
            for (const item of obj) {
                const r = findField(item, key, depth + 1);
                if (r) return r;
            }
        }
        return '';
    }

    const description = findField(apiData, 'series_intro');
    console.log(`Description from API: ${description.substring(0, 100)}...`);

    // Update DB with correct title and description
    const result = await p.drama.update({
        where: { id: 'cmleexukt0383hx5ewjk5efxh' },
        data: {
            title: 'Jenderal Terakhir',
            description: description || 'Di dunia kultivasi, Rizky menggantikan adiknya masuk militer dan naik jadi Jenderal Enam Bintang.',
        }
    });

    console.log(`\n✅ Updated: "${result.title}"`);
    console.log(`   Description: ${result.description?.substring(0, 80)}...`);

    // Also update local metadata
    const metaPath = 'd:/kingshortid/scripts/melolo-scraper/r2_ready/melolo/drama-09750069/metadata.json';
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
    meta.title = 'Jenderal Terakhir';
    meta.description = result.description;
    fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2));
    console.log('   Local metadata also updated ✅');

    await p.$disconnect();
}
main();

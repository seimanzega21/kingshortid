import fs from 'fs';
import path from 'path';
import { Stream } from 'stream';
import { finished } from 'stream/promises';
import { Readable } from 'stream';

const BASE_URL = 'https://stream.shortlovers.id/si_kembar_lima_bantu_ayah_kejar_ibu/si_kembar_lima_bantu_ayah_kejar_ibu_ep_1';
const OUT_DIR = path.join(__dirname, '../temp_segments');

if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR);
}

async function downloadFile(filename: string) {
    const url = `${BASE_URL}/${filename}`;
    const dest = path.join(OUT_DIR, filename);
    console.log(`Downloading ${url}...`);

    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.statusText}`);

    const fileStream = fs.createWriteStream(dest, { flags: 'wx' });
    // @ts-ignore
    await finished(Readable.fromWeb(res.body).pipe(fileStream));
    console.log(`Saved to ${dest}`);
}

async function main() {
    try {
        await downloadFile('shortlovers_000004.ts');
        await downloadFile('shortlovers_000005.ts');
    } catch (e) {
        console.error(e);
    }
}

main();

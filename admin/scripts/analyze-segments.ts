import fs from 'fs';
import path from 'path';
import mediainfo from 'mediainfo.js';

const SEGMENTS_DIR = path.join(__dirname, '../temp_segments');

async function analyze() {
    const files = fs.readdirSync(SEGMENTS_DIR).filter(f => f.endsWith('.ts'));
    console.log(`Analyzing ${files.length} segments in ${SEGMENTS_DIR}...`);

    for (const file of files) {
        const filePath = path.join(SEGMENTS_DIR, file);
        const fileHandle = await fs.promises.open(filePath, 'r');
        const size = (await fileHandle.stat()).size;

        const readChunk = async (size: number, offset: number) => {
            const buffer = Buffer.alloc(size);
            await fileHandle.read(buffer, 0, size, offset);
            return buffer; // Ensure this returns a Uint8Array-compatible buffer
        };

        try {
            const info = await mediainfo({ format: 'object', coverData: false });
            const result = await info.analyzeData(() => size, readChunk);

            // Extract Duration from General track
            // @ts-ignore
            const general = result.media?.track?.find(t => t['@type'] === 'General');
            if (general) {
                console.log(`\n📄 File: ${file}`);
                // @ts-ignore
                console.log(`   Duration: ${general.Duration}s`);
                // @ts-ignore
                console.log(`   Format: ${general.Format}`);
            }
        } catch (e: any) {
            console.error(`Error analyzing ${file}: ${e.message}`);
        } finally {
            await fileHandle.close();
        }
    }
}

analyze();

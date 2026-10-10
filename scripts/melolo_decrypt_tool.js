const fs = require('fs');
const { webcrypto } = require('crypto');
const crypto = webcrypto;

function readUint32(buf, offset) {
    return (buf[offset] << 24 | buf[offset + 1] << 16 | buf[offset + 2] << 8 | buf[offset + 3]) >>> 0;
}

function writeTag(buf, offset, str) {
    for (let i = 0; i < 4; i++) buf[offset + i] = str.charCodeAt(i);
}

function readTag(buf, offset) {
    return String.fromCharCode(buf[offset], buf[offset + 1], buf[offset + 2], buf[offset + 3]);
}

function parseBoxes(buf, start, end) {
    const boxes = [];
    let pos = start;
    while (pos + 8 <= end) {
        const size = readUint32(buf, pos);
        if (size < 8 || pos + size > end) break;
        boxes.push({
            offset: pos,
            size: size,
            tag: readTag(buf, pos + 4),
            bodyOff: pos + 8
        });
        pos += size;
    }
    return boxes;
}

function findBoxPath(buf, start, end, ...tags) {
    let s = start, e = end, match = null;
    for (const tag of tags) {
        match = null;
        for (const b of parseBoxes(buf, s, e)) {
            if (b.tag === tag) {
                match = b;
                s = b.bodyOff;
                e = b.offset + b.size;
                break;
            }
        }
        if (!match) return null;
    }
    return match;
}

function parseTrackInfo(buf, moov) {
    const tracks = [];
    for (const b of parseBoxes(buf, moov.bodyOff, moov.offset + moov.size)) {
        if (b.tag !== 'trak') continue;
        const mdia = findBoxPath(buf, b.bodyOff, b.offset + b.size, 'mdia');
        if (!mdia) continue;
        const hdlr = findBoxPath(buf, mdia.bodyOff, mdia.offset + mdia.size, 'hdlr');
        if (!hdlr) continue;
        const handlerType = readTag(buf, hdlr.offset + 16);
        if (handlerType !== 'vide' && handlerType !== 'soun') continue;

        const stbl = findBoxPath(buf, mdia.bodyOff, mdia.offset + mdia.size, 'minf', 'stbl');
        if (!stbl) continue;

        const findInStbl = (tag) => {
            for (const box of parseBoxes(buf, stbl.bodyOff, stbl.offset + stbl.size)) {
                if (box.tag === tag) return box;
            }
            return null;
        };

        const stsz = findInStbl('stsz');
        const stsc = findInStbl('stsc');
        const stco = findInStbl('stco');
        const co64 = findInStbl('co64');
        const senc = findInStbl('senc');
        if (!stsz || !stsc || (!stco && !co64)) continue;

        const defaultSampleSize = readUint32(buf, stsz.bodyOff + 4);
        const sampleCount = readUint32(buf, stsz.bodyOff + 8);
        const sampleSizes = new Array(sampleCount);
        if (defaultSampleSize === 0) {
            for (let i = 0; i < sampleCount; i++) sampleSizes[i] = readUint32(buf, stsz.bodyOff + 12 + 4 * i);
        } else {
            sampleSizes.fill(defaultSampleSize);
        }

        let chunkOffsets;
        if (stco) {
            const count = readUint32(buf, stco.bodyOff + 4);
            chunkOffsets = new Array(count);
            for (let i = 0; i < count; i++) chunkOffsets[i] = readUint32(buf, stco.bodyOff + 8 + 4 * i);
        } else {
            const count = readUint32(buf, co64.bodyOff + 4);
            chunkOffsets = new Array(count);
            for (let i = 0; i < count; i++) {
                const off = co64.bodyOff + 8 + 8 * i;
                chunkOffsets[i] = 0x100000000 * readUint32(buf, off) + readUint32(buf, off + 4);
            }
        }

        const stscCount = readUint32(buf, stsc.bodyOff + 4);
        const stscEntries = [];
        for (let i = 0; i < stscCount; i++) {
            stscEntries.push({
                firstChunk: readUint32(buf, stsc.bodyOff + 8 + 12 * i),
                spc: readUint32(buf, stsc.bodyOff + 12 + 12 * i)
            });
        }

        const sampleOffsets = [];
        let sIdx = 0;
        for (let c = 0; c < chunkOffsets.length && sIdx < sampleCount; c++) {
            let spc = 1;
            for (const e of stscEntries) {
                if (c + 1 >= e.firstChunk) spc = e.spc;
                else break;
            }
            let curOff = chunkOffsets[c];
            for (let s = 0; s < spc && sIdx < sampleCount; s++) {
                sampleOffsets.push(curOff);
                curOff += sampleSizes[sIdx];
                sIdx++;
            }
        }

        const ivs = [];
        if (senc) {
            const flags = buf[senc.bodyOff + 1] << 16 | buf[senc.bodyOff + 2] << 8 | buf[senc.bodyOff + 3];
            const sampleCountSenc = readUint32(buf, senc.bodyOff + 4);
            let sencPos = senc.bodyOff + 8;
            for (let i = 0; i < sampleCountSenc; i++) {
                ivs.push(new Uint8Array(buf.buffer, buf.byteOffset + sencPos, 8));
                sencPos += 8;
                if (flags & 2) {
                    const subsCount = buf[sencPos] << 8 | buf[sencPos + 1];
                    sencPos += 2 + subsCount * 6;
                }
            }
        }

        if (ivs.length > 0) {
            tracks.push({
                sampleOffs: sampleOffsets,
                sizes: sampleSizes,
                ivs: ivs
            });
        }
    }
    return tracks;
}

async function decryptTrackSamples(buf, track, cryptoKey, from, to) {
    const promises = [];
    for (let i = from; i < to; i++) {
        const counter = new Uint8Array(16);
        counter.set(track.ivs[i], 0);
        const sOff = track.sampleOffs[i];
        const sSize = track.sizes[i];
        const sampleData = buf.buffer.slice(buf.byteOffset + sOff, buf.byteOffset + sOff + sSize);
        promises.push(
            crypto.subtle.decrypt({ name: 'AES-CTR', counter: counter, length: 64 }, cryptoKey, sampleData)
                .then(dec => {
                    buf.set(new Uint8Array(dec), sOff);
                })
        );
    }
    return Promise.all(promises);
}

function unprotectBoxes(buf, moov) {
    const replacements = {
        encv: 'hvc1',
        enca: 'mp4a',
        sinf: 'free',
        schm: 'free',
        schi: 'free',
        senc: 'free',
        saio: 'free',
        saiz: 'free',
        tenc: 'free',
        frma: 'free',
        pssh: 'free'
    };

    const end = moov.offset + moov.size;
    for (let i = moov.offset + 4; i + 4 <= end; i++) {
        const tag = readTag(buf, i);
        if (tag in replacements) {
            const size = readUint32(buf, i - 4);
            if (size >= 8 && size <= end - i + 4) {
                writeTag(buf, i, replacements[tag]);
            }
        }
    }

    let pos = 0;
    while (pos + 8 <= buf.length) {
        const size = readUint32(buf, pos);
        if (size < 8 || pos + size > buf.length) break;
        if (readTag(buf, pos + 4) === 'pssh') {
            writeTag(buf, pos + 4, 'free');
        }
        pos += size;
    }
}

async function decryptMeloloBuffer(buf, hexKey) {
    const rawKey = new Uint8Array(hexKey.match(/.{2}/g).map(e => parseInt(e, 16)));
    const cryptoKey = await crypto.subtle.importKey('raw', rawKey, { name: 'AES-CTR' }, false, ['decrypt']);

    const moov = findBoxPath(buf, 0, buf.length, 'moov');
    if (!moov) throw new Error('No moov box found in MP4');

    const tracks = parseTrackInfo(buf, moov);
    if (!tracks || tracks.length === 0) throw new Error('No encrypted tracks found');

    for (const trk of tracks) {
        const total = Math.min(trk.sampleOffs.length, trk.ivs.length);
        const batchSize = 500;
        for (let i = 0; i < total; i += batchSize) {
            const end = Math.min(i + batchSize, total);
            await decryptTrackSamples(buf, trk, cryptoKey, i, end);
        }
    }

    unprotectBoxes(buf, moov);
    return buf;
}

async function main() {
    const inPath = process.argv[2];
    const outPath = process.argv[3];
    const hexKey = process.argv[4];

    if (!inPath || !outPath || !hexKey) {
        console.error('Usage: node melolo_decrypt_tool.js <input.mp4> <output.mp4> <hex_key>');
        process.exit(1);
    }

    const inputBuf = fs.readFileSync(inPath);
    await decryptMeloloBuffer(inputBuf, hexKey);
    fs.writeFileSync(outPath, inputBuf);
    console.log(`DECRYPT_OK ${inputBuf.length}`);
}

main().catch(err => {
    console.error('DECRYPT_ERROR:', err);
    process.exit(1);
});

const fs = require('fs');

const BROKEN = [
    { title: "Tangi Penyesalan Bos Cantik", id: "cmlkd3jl408sr13mdwb3z00xe" },
    { title: "Tangkap Harta Karun Di Kampung", id: "cmlkd3jny08vk13mde1sm5xpe" },
    { title: "Sadar Akan Realita", id: "cmlkd335g082m13md4l8sy2gk" },
    { title: "Salah Meja Nikah Dengan Dokter", id: "cmlkd33al084b13mddoez6bxe" },
    { title: "Nikah Instan Cinta Tak Terduga", id: "cmlkd2nkk06ep13mdctgduhwg" },
    { title: "Harta Tahta Dan Ketulusan", id: "cmlkd1mja039a13mdziuyhnn0" },
    { title: "Diusir Dari Rumah Saya Mewarisi Miliaran", id: "cmlkd1a9z02np13md4skw9u6z" },
    { title: "Dimanja Habis Habisan Oleh Bos", id: "cmlkd18oz026w13md09zpb4w4" },
];

async function main() {
    const r = await fetch('https://kingshortid-api.toonplay-seiman.workers.dev/api/dramas?limit=500');
    const d = await r.json();
    const all = Array.isArray(d) ? d : d.dramas || [];

    let out = "=== DUPLICATE CHECK ===\n\n";
    const toDelete = [];
    const toFixCover = [];

    for (const broken of BROKEN) {
        const matches = all.filter(x => x.title === broken.title);
        out += `[${broken.title}] — ${matches.length} match(es)\n`;
        out += `  Broken ID: ${broken.id}\n`;

        if (matches.length > 1) {
            out += `  >>> DUPLICATE — delete broken copy\n`;
            toDelete.push(broken);
            matches.forEach(m => {
                const isBroken = m.id === broken.id;
                out += `    ${isBroken ? 'X BROKEN' : 'V GOOD'}: ${m.id} | cover: ${m.cover}\n`;
            });
        } else {
            out += `  >>> UNIQUE — fix cover only\n`;
            toFixCover.push(broken);
        }
        out += `\n`;
    }

    // Ahli Pengobatan Sakti
    out += "\n=== AHLI PENGOBATAN SAKTI ===\n\n";
    const ahli = all.filter(x => x.title && x.title.includes("Ahli Pengobatan"));
    if (ahli.length) {
        ahli.forEach(a => {
            out += `  Title: ${a.title}\n`;
            out += `  ID: ${a.id}\n`;
            out += `  Cover: ${a.cover}\n`;
            out += `  TotalEps: ${a.totalEpisodes || '?'}\n`;
        });
    } else {
        out += "  Not found in DB\n";
    }

    out += `\n=== SUMMARY ===\n`;
    out += `To DELETE (duplicates): ${toDelete.length}\n`;
    toDelete.forEach(d => out += `  - ${d.title} (${d.id})\n`);
    out += `To FIX COVER (unique): ${toFixCover.length}\n`;
    toFixCover.forEach(d => out += `  - ${d.title} (${d.id})\n`);

    fs.writeFileSync('d:/kingshortid/scripts/duplicate_report.txt', out);
    console.log('Written to duplicate_report.txt');
}
main();

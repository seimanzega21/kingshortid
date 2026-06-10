const postgres = require('postgres');
const sql = postgres('postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres');
const fs = require('fs');

async function run() {
    const pending = await sql`SELECT id, title, cover FROM dramas WHERE is_active = false`;
    console.log(`Found ${pending.length} pending dramas`);
    
    const toDelete = pending.filter(d => d.title.includes('[Versi Dub]'));
    console.log(`Found ${toDelete.length} pending [Versi Dub] dramas to delete.`);
    
    fs.writeFileSync('to_delete.json', JSON.stringify(toDelete, null, 2));
    
    for (const d of toDelete) {
        console.log(`- ${d.title} (ID: ${d.id})`);
    }
    
    process.exit(0);
}

run().catch(console.error);

const postgres = require('postgres');
const sql = postgres('postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres');
const fs = require('fs');

async function run() {
    const toDelete = JSON.parse(fs.readFileSync('to_delete.json', 'utf8'));
    
    if (toDelete.length === 0) {
        console.log("Nothing to delete.");
        process.exit(0);
    }
    
    const ids = toDelete.map(d => d.id);
    
    // Delete dramas (cascade will handle episodes, subtitles, etc)
    const res = await sql`DELETE FROM dramas WHERE id IN ${sql(ids)}`;
    console.log(`Successfully deleted ${res.count} pending duplicate dramas.`);
    
    process.exit(0);
}

run().catch(console.error);

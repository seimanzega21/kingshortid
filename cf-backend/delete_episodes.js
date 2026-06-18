const postgres = require('postgres');
const sql = postgres('postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:5435/postgres');

async function run() {
    const dramaId = 'yfgd414ly5jh0uv690cxj0j9';
    
    console.log(`🧹 Cleaning up episodes for drama ID: ${dramaId}...`);
    
    // 1. Delete all subtitles for these episodes
    const subtitlesRes = await sql`
        DELETE FROM subtitles 
        WHERE episode_id IN (
            SELECT id FROM episodes WHERE drama_id = ${dramaId}
        )
    `;
    console.log(`   ✓ Deleted ${subtitlesRes.count} subtitles.`);
    
    // 2. Delete all episodes
    const episodesRes = await sql`
        DELETE FROM episodes 
        WHERE drama_id = ${dramaId}
    `;
    console.log(`   ✓ Deleted ${episodesRes.count} episodes.`);
    
    // 3. Reset totalEpisodes count in dramas table
    const dramasRes = await sql`
        UPDATE dramas 
        SET total_episodes = 0, updated_at = NOW() 
        WHERE id = ${dramaId}
    `;
    console.log(`   ✓ Reset total_episodes to 0 for drama ID: ${dramaId}.`);
    
    console.log("🧹 Cleanup complete!");
    process.exit(0);
}

run().catch(err => {
    console.error("❌ Cleanup failed:", err);
    process.exit(1);
});

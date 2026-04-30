import pg from 'pg';
const { Client } = pg;
import dotenv from 'dotenv';
dotenv.config({ path: '.env' });

async function debugDashboard() {
    const client = new Client({
        connectionString: process.env.DATABASE_URL
    });

    try {
        await client.connect();
        console.log("Connected to DB.");

        console.log("Checking basic stats...");
        const statsRes = await client.query(`
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE role = 'user') as active_users,
                (SELECT COUNT(*) FROM dramas) as total_dramas,
                (SELECT COUNT(*) FROM dramas WHERE is_active = true) as active_dramas,
                (SELECT COUNT(*) FROM dramas WHERE is_active = false) as inactive_dramas,
                (SELECT COUNT(*) FROM episodes) as total_episodes
        `);
        console.log("Stats rows:", statsRes.rows);

        console.log("\nChecking online users...");
        const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
        const onlineRes = await client.query(`SELECT count(*) FROM users WHERE last_seen >= $1`, [fiveMinAgo]);
        console.log("Online count:", onlineRes.rows[0].count);

        console.log("\nChecking health query...");
        const healthRes = await client.query(`
            SELECT 
                COUNT(*) FILTER (WHERE description = '' OR description = title OR length(description) < 10) as no_desc,
                COUNT(*) FILTER (WHERE cover = '') as no_cover,
                COUNT(*) FILTER (WHERE total_episodes = 0) as no_eps,
                COUNT(*) FILTER (WHERE genres::jsonb = '[]'::jsonb OR genres::jsonb = '["Drama"]'::jsonb OR jsonb_array_length(genres::jsonb) = 0) as generic_genre
            FROM dramas
            WHERE is_active = true
        `);
        console.log("Health rows:", healthRes.rows);

    } catch (e) {
        console.error("Query failed:", e.message);
    } finally {
        await client.end();
    }
}

debugDashboard();

import { getDb } from './src/db/index.js';
import { sql, gte, eq, and, or, desc } from 'drizzle-orm';
import { users, dramas, episodes } from './src/db/schema.js';
import dotenv from 'dotenv';
dotenv.config({ path: '.env' });

async function debugDashboard() {
    const url = process.env.SUPABASE_URL;
    const pass = process.env.SUPABASE_DB_PASSWORD;
    const db = getDb(url, pass);

    console.log("Checking basic stats...");
    try {
        const statsQuery = await db.execute(sql`
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE role = 'user') as active_users,
                (SELECT COUNT(*) FROM dramas) as total_dramas,
                (SELECT COUNT(*) FROM dramas WHERE is_active = true) as active_dramas,
                (SELECT COUNT(*) FROM dramas WHERE is_active = false) as inactive_dramas,
                (SELECT COUNT(*) FROM episodes) as total_episodes
        `);
        console.log("Stats Query Result Type:", typeof statsQuery);
        console.log("Stats Query Result Keys:", Object.keys(statsQuery));
        // console.log("Stats Query Result:", JSON.stringify(statsQuery, null, 2));
    } catch (e) {
        console.error("Basic stats failed:", e.message);
    }

    console.log("\nChecking online users...");
    try {
        const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000);
        const onlineResult = await db.select({ count: sql`count(*)` })
            .from(users)
            .where(gte(users.lastSeen, fiveMinAgo))
            .limit(1);
        console.log("Online result:", onlineResult);
    } catch (e) {
        console.error("Online users failed:", e.message);
    }

    console.log("\nChecking health query...");
    try {
        const healthQuery = await db.execute(sql`
            SELECT 
                COUNT(*) FILTER (WHERE description = '' OR description = title OR length(description) < 10) as no_desc,
                COUNT(*) FILTER (WHERE cover = '') as no_cover,
                COUNT(*) FILTER (WHERE total_episodes = 0) as no_eps,
                COUNT(*) FILTER (WHERE genres::jsonb = '[]'::jsonb OR genres::jsonb = '["Drama"]'::jsonb OR jsonb_array_length(genres::jsonb) = 0) as generic_genre
            FROM dramas
            WHERE is_active = true
        `);
        console.log("Health query result:", healthQuery);
    } catch (e) {
        console.error("Health query failed:", e.message);
    }
}

debugDashboard();

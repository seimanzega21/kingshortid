import pg from 'pg';
const { Client } = pg;
import dotenv from 'dotenv';
dotenv.config({ path: '.env.production' });

async function checkSchema() {
    const client = new Client({
        connectionString: process.env.DATABASE_URL.replace('SUPABASE_DB_PASSWORD', process.env.SUPABASE_DB_PASSWORD)
            .replace('supabase-db-og8gwooogk480gcws0o84ssc', '141.11.160.187')
    });

    try {
        await client.connect();
        console.log("Connected.");
        const res = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'dramas' AND column_name IN ('genres', 'tag_list', 'cast')
        `);
        console.log("Columns:", res.rows);
    } catch (e) {
        console.error("Failed:", e.message);
    } finally {
        await client.end();
    }
}

checkSchema();

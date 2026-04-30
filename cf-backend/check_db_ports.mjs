import pg from 'pg';
const { Client } = pg;
import dotenv from 'dotenv';
dotenv.config({ path: '.env.production' });

async function checkSchema() {
    const dbPassword = process.env.SUPABASE_DB_PASSWORD;
    const host = '141.11.160.187';
    // Try both 5432 and 6543
    const ports = [5432, 6543];
    
    for (const port of ports) {
        console.log(`Trying port ${port}...`);
        const client = new Client({
            connectionString: `postgresql://postgres:${dbPassword}@${host}:${port}/postgres`
        });
        try {
            await client.connect();
            console.log(`Connected on port ${port}.`);
            const res = await client.query(`SELECT 1`);
            console.log("Success.");
            await client.end();
            return;
        } catch (e) {
            console.error(`Port ${port} failed:`, e.message);
        }
    }
}

checkSchema();

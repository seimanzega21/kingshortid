const path = require('path');
const fs = require('fs');

// Borrow postgres module from cf-backend
const cfBackendPath = path.join(__dirname, '..', 'cf-backend');
const nodeModulesPath = path.join(cfBackendPath, 'node_modules');
if (fs.existsSync(nodeModulesPath)) {
    module.paths.push(nodeModulesPath);
}

const postgres = require('postgres');

// Database Connection PRODUKSI (Supabase)
const connectionString = 'postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres';
const sql = postgres(connectionString);

async function reset() {
    const targetEmail = 'seimanzega92@gmail.com';
    try {
        console.log(`⏳ [PRODUKSI] Menembak langsung ke Supabase untuk meriset saldo: ${targetEmail}...`);
        
        const result = await sql`
            UPDATE users 
            SET coins = 0, purchased_coins = 0, updated_at = NOW() 
            WHERE email = ${targetEmail}
            RETURNING id, email, coins, purchased_coins
        `;
        
        if (result.length > 0) {
            console.log('✅ BERHASIL! Saldo di DATABASE PRODUKSI sudah menjadi 0.');
            console.table(result);
        } else {
            console.log(`❌ GAGAL: Email '${targetEmail}' tidak ditemukan di Database Produksi.`);
        }
    } catch (err) {
        console.error('❌ ERROR DATABASE:', err.message);
    } finally {
        await sql.end();
        process.exit();
    }
}

reset();

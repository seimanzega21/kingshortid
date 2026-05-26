const { Client } = require('pg');
const client = new Client({ connectionString: 'postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres' });
client.connect().then(() => {
    return client.query(`
        CREATE TABLE IF NOT EXISTS app_settings (
            id text PRIMARY KEY DEFAULT 'global',
            banner_mode text NOT NULL DEFAULT 'auto',
            banner_rotation_days int NOT NULL DEFAULT 2,
            updated_at timestamp NOT NULL DEFAULT NOW()
        );
        INSERT INTO app_settings (id, banner_mode, banner_rotation_days)
        VALUES ('global', 'auto', 2)
        ON CONFLICT (id) DO NOTHING;
    `);
}).then(() => {
    console.log('Table created successfully');
    client.end();
}).catch((e) => {
    console.error(e);
    client.end();
});

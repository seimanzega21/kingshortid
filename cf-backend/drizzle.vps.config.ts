import { defineConfig } from 'drizzle-kit';

export default defineConfig({
    schema: './src/db/schema.ts',
    out: './drizzle',
    dialect: 'postgresql',
    dbCredentials: {
        url: process.env.DATABASE_URL ||
            `postgresql://postgres:${process.env.SUPABASE_DB_PASSWORD}@${(process.env.SUPABASE_URL || '').replace(/^https?:\/\//, '').split(':')[0]}:5432/postgres`,
    },
    verbose: true,
    strict: false,
});

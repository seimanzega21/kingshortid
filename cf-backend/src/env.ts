/**
 * Environment adapter — replaces Cloudflare `c.env.X` with `process.env.X`
 * Used by VPS deployment (Bun/Node), not by Cloudflare Workers.
 */
export const serverEnv = {
    get JWT_SECRET() {
        return process.env.JWT_SECRET || 'fallback-secret-key';
    },
    get SUPABASE_URL() {
        return process.env.SUPABASE_URL || '';
    },
    get SUPABASE_DB_PASSWORD() {
        return process.env.SUPABASE_DB_PASSWORD || '';
    },
    get ADMIN_API_KEY() {
        return process.env.ADMIN_API_KEY || '';
    },
};

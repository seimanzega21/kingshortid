/**
 * Environment adapter — replaces Cloudflare `c.env.X` with `process.env.X`
 * Used by VPS deployment (Bun/Node), not by Cloudflare Workers.
 */

function requireEnv(key: string): string {
    const value = process.env[key];
    if (!value) throw new Error(`[ENV] Required environment variable "${key}" is not set. Check .env.production.`);
    return value;
}

export const serverEnv = {
    get JWT_SECRET() {
        return requireEnv('JWT_SECRET');
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
    get FIREBASE_SERVICE_ACCOUNT() {
        return process.env.FIREBASE_SERVICE_ACCOUNT || '';
    },
    get MIDTRANS_SERVER_KEY() {
        return process.env.MIDTRANS_SERVER_KEY || '';
    },
    get MIDTRANS_IS_PRODUCTION() {
        return process.env.MIDTRANS_IS_PRODUCTION || 'false';
    },
};

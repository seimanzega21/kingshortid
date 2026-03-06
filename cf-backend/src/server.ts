/**
 * VPS Entrypoint — Bun HTTP Server
 * Replaces Cloudflare Workers runtime for self-hosted deployment.
 */
import app from './index-vps';

const PORT = parseInt(process.env.PORT || '3000');
const HOST = process.env.HOST || '0.0.0.0';

const server = Bun.serve({
    port: PORT,
    hostname: HOST,
    fetch: app.fetch,
});

console.log(`🚀 KingShortID API running on http://${HOST}:${server.port}`);
console.log(`   DB: ${process.env.SUPABASE_URL || 'not set'}`);
console.log(`   Env: ${process.env.NODE_ENV || 'development'}`);

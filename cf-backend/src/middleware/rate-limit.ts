import { Context, Next } from 'hono';
import type { Env } from './auth';

// Simple in-memory rate limiter for Workers
// Note: In Workers, each isolate has its own memory, so this is per-isolate.
const rateLimitStore = new Map<string, { count: number; resetAt: number }>();
let lastCleanup = Date.now();

function cleanupStaleEntries() {
    const now = Date.now();
    if (now - lastCleanup < 5 * 60 * 1000) return;
    lastCleanup = now;
    for (const [key, record] of rateLimitStore) {
        if (now > record.resetAt) {
            rateLimitStore.delete(key);
        }
    }
}

function getClientIp(c: Context<Env>): string {
    const cfIp = c.req.header('CF-Connecting-IP');
    if (cfIp) return cfIp.trim();

    const forwarded = c.req.header('X-Forwarded-For');
    if (forwarded) {
        // X-Forwarded-For can contain comma-separated IPs (client, proxy1, proxy2). Extract the first IP.
        const firstIp = forwarded.split(',')[0].trim();
        if (firstIp) return firstIp;
    }

    const realIp = c.req.header('X-Real-IP');
    if (realIp) return realIp.trim();

    return 'unknown';
}

function createRateLimiter(maxRequests: number, windowMs: number) {
    return async (c: Context<Env>, next: Next) => {
        cleanupStaleEntries();
        const key = getClientIp(c);
        const now = Date.now();

        const record = rateLimitStore.get(key);

        if (!record || now > record.resetAt) {
            rateLimitStore.set(key, { count: 1, resetAt: now + windowMs });
            await next();
            return;
        }

        if (record.count >= maxRequests) {
            return c.json({
                error: 'Too many requests',
                message: 'Terlalu banyak permintaan. Silakan coba lagi nanti.',
                retryAfter: Math.ceil((record.resetAt - now) / 1000),
            }, 429);
        }

        record.count++;
        await next();
    };
}

// Rate limiters — dinaikkan batasnya agar user mobile normal atau WiFi publik tidak terkena 429
export const apiLimiter = createRateLimiter(300, 60 * 1000);      // 300 req/min (sebelumnya 100)
export const authLimiter = createRateLimiter(15, 60 * 1000);       // 15 req/min (sebelumnya 5)
export const rewardLimiter = createRateLimiter(30, 60 * 1000);    // 30 req/min
export const sensitiveLimiter = createRateLimiter(20, 60 * 1000); // 20 req/min

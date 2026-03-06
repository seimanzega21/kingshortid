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

function createRateLimiter(maxRequests: number, windowMs: number) {
    return async (c: Context<Env>, next: Next) => {
        cleanupStaleEntries();
        const key = c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For') || 'unknown';
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

// Rate limiters matching the original Express backend
export const apiLimiter = createRateLimiter(100, 60 * 1000);      // 100 req/min
export const authLimiter = createRateLimiter(5, 60 * 1000);       // 5 req/min
export const rewardLimiter = createRateLimiter(3, 60 * 1000);     // 3 req/min
export const sensitiveLimiter = createRateLimiter(10, 60 * 1000); // 10 req/min

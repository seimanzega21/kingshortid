import { Context, Next } from 'hono';
import * as jose from 'jose';
import { eq, and } from 'drizzle-orm';
import { getDb } from '../db';
import { users } from '../db/schema';

export interface JWTPayload {
    id: string;
    role: string;
}

export type Env = {
    Bindings: {
        SUPABASE_URL: string;
        SUPABASE_DB_PASSWORD: string;
        JWT_SECRET: string;
    };
    Variables: {
        user: typeof users.$inferSelect;
    };
};

function getSecret(c: Context<Env>) {
    return new TextEncoder().encode(c.env.JWT_SECRET || 'fallback-secret-key');
}

export async function generateToken(c: Context<Env>, payload: JWTPayload): Promise<string> {
    return new jose.SignJWT(payload as unknown as jose.JWTPayload)
        .setProtectedHeader({ alg: 'HS256' })
        .setExpirationTime('7d')
        .sign(getSecret(c));
}

export async function verifyToken(c: Context<Env>, token: string): Promise<JWTPayload | null> {
    try {
        const { payload } = await jose.jwtVerify(token, getSecret(c));
        return payload as unknown as JWTPayload;
    } catch {
        return null;
    }
}

export async function getAuthUser(c: Context<Env>) {
    const authHeader = c.req.header('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return null;

    const token = authHeader.replace('Bearer ', '');
    const payload = await verifyToken(c, token);
    if (!payload) return null;

    const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
    const result = await db.select().from(users)
        .where(and(eq(users.id, payload.id), eq(users.isActive, true)))
        .limit(1);

    return result[0] || null;
}

// Middleware: require authentication
export async function requireAuth(c: Context<Env>, next: Next) {
    const user = await getAuthUser(c);
    if (!user) {
        return c.json({ error: 'Authentication required' }, 401);
    }
    c.set('user', user);
    await next();
}

// Middleware: require admin role
export async function requireAdmin(c: Context<Env>, next: Next) {
    const user = await getAuthUser(c);
    if (!user || user.role !== 'admin') {
        return c.json({ error: 'Admin access required' }, 403);
    }
    c.set('user', user);
    await next();
}

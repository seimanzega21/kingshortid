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
        ADMIN_API_KEY: string;
        REVENUECAT_WEBHOOK_SECRET: string;
        REVENUECAT_SECRET_KEY: string;
        MIDTRANS_SERVER_KEY: string;
        MIDTRANS_IS_PRODUCTION: string;
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

    const user = result[0] || null;

    if (user) {
        const now = new Date();
        const lastSeenTime = user.lastSeen ? new Date(user.lastSeen).getTime() : 0;
        const needsLastSeenUpdate = now.getTime() - lastSeenTime > 120000;
        
        let vipExpired = false;
        if (user.vipStatus && user.vipExpiry && new Date(user.vipExpiry).getTime() < now.getTime()) {
            user.vipStatus = false;
            vipExpired = true;
        }

        let adFreeExpired = false;
        if (user.adFreeExpiry && new Date(user.adFreeExpiry).getTime() < now.getTime()) {
            adFreeExpired = true;
        }

        if (needsLastSeenUpdate || vipExpired || adFreeExpired) {
            const updateData: any = {};
            if (needsLastSeenUpdate) {
                updateData.lastSeen = now;
                user.lastSeen = now;
            }
            if (vipExpired) {
                updateData.vipStatus = false;
            }
            if (adFreeExpired) {
                updateData.adFreeExpiry = null;
            }
            db.update(users).set(updateData).where(eq(users.id, user.id)).catch(() => {});
        }
        
        (user as any).isAdFreeActive = user.adFreeExpiry ? new Date(user.adFreeExpiry).getTime() > now.getTime() : false;
    }

    return user;
}

export async function requireAuth(c: Context<Env>, next: Next) {
    const user = await getAuthUser(c);
    if (!user) {
        return c.json({ error: 'Authentication required' }, 401);
    }
    c.set('user', user);
    await next();
}

export async function requireAdmin(c: Context<Env>, next: Next) {
    const adminKey = c.req.header('X-Admin-Key');
    if (adminKey && adminKey === c.env.ADMIN_API_KEY) {
        return await next();
    }

    const user = await getAuthUser(c);
    if (!user || user.role !== 'admin') {
        return c.json({ error: 'Admin access required' }, 403);
    }
    c.set('user', user);
    await next();
}

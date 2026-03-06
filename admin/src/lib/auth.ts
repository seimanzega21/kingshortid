import jwt from 'jsonwebtoken';
import { NextRequest } from 'next/server';
import prisma from './prisma';

const JWT_SECRET = process.env.JWT_SECRET || 'fallback-secret';

export interface JWTPayload {
    id: string;
    role: string;
}

export function generateToken(payload: JWTPayload): string {
    return jwt.sign(payload, JWT_SECRET, { expiresIn: '7d' });
}

export function verifyToken(token: string): JWTPayload | null {
    try {
        return jwt.verify(token, JWT_SECRET) as JWTPayload;
    } catch {
        return null;
    }
}

export async function getAuthUser(request: NextRequest) {
    const authHeader = request.headers.get('authorization');
    if (!authHeader?.startsWith('Bearer ')) {
        return null;
    }

    const token = authHeader.replace('Bearer ', '');
    const payload = verifyToken(token);
    if (!payload) {
        return null;
    }

    const user = await prisma.user.findUnique({
        where: { id: payload.id, isActive: true },
    });

    return user;
}

export async function requireAuth(request: NextRequest) {
    const user = await getAuthUser(request);
    if (!user) {
        throw new Error('Authentication required');
    }
    return user;
}

export async function requireAdmin(request: NextRequest) {
    const user = await requireAuth(request);
    if (user.role !== 'admin') {
        throw new Error('Admin access required');
    }
    return user;
}

// Aliases for Sprint 3 compatibility
export const verifyAuth = getAuthUser;
export const verifyAdmin = async (request: NextRequest) => {
    const user = await getAuthUser(request);
    return user?.role === 'admin';
};


import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { generateToken } from '@/lib/auth';
import bcrypt from 'bcryptjs';

// POST /api/auth/login (General User)
export async function POST(request: NextRequest) {
    try {
        const { email, password } = await request.json();

        // 1. Find User
        const user = await prisma.user.findUnique({ where: { email } });
        if (!user) {
            return NextResponse.json({ message: 'Email tidak ditemukan' }, { status: 404 });
        }

        // 2. Check Password (if exists)
        if (!user.password && user.provider !== 'local') {
            return NextResponse.json({ message: 'Silakan login menggunakan Google/Facebook' }, { status: 400 });
        }

        const isValid = await bcrypt.compare(password, user.password || '');
        if (!isValid) {
            return NextResponse.json({ message: 'Password salah' }, { status: 401 });
        }

        if (!user.isActive) {
            return NextResponse.json({ message: 'Akun dinonaktifkan' }, { status: 403 });
        }

        // 3. Generate Token with only required fields
        const token = generateToken({
            id: user.id,
            role: user.role,
        });

        // 4. Return minimal user data
        return NextResponse.json({
            token,
            user: {
                id: user.id,
                email: user.email,
                name: user.name,
                avatar: user.avatar,
                coins: user.coins,
                vipStatus: user.vipStatus,
                vipExpiry: user.vipExpiry
            }
        });

    } catch (error) {
        return NextResponse.json({ message: 'Login Error' }, { status: 500 });
    }
}

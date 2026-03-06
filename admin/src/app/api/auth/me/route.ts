import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import prisma from '@/lib/prisma';
import bcrypt from 'bcryptjs';

// GET /api/auth/me
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const dbUser = await prisma.user.findUnique({
            where: { id: user.id },
            select: {
                id: true,
                email: true,
                name: true,
                avatar: true,
                coins: true,
                vipStatus: true,
                vipExpiry: true,
                isGuest: true,
                guestId: true,
            }
        });

        return NextResponse.json(dbUser);
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

// PUT /api/auth/me - Update profile (name, avatar, password)
export async function PUT(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const body = await request.json();
        const { name, avatar, currentPassword, newPassword } = body;

        const updateData: any = {};

        if (name?.trim()) updateData.name = name.trim();
        if (avatar) updateData.avatar = avatar;

        // Password change
        if (newPassword) {
            if (!currentPassword) {
                return NextResponse.json({ message: 'Password lama diperlukan' }, { status: 400 });
            }

            const dbUser = await prisma.user.findUnique({ where: { id: user.id } });
            if (!dbUser?.password) {
                return NextResponse.json({ message: 'Akun ini tidak menggunakan password' }, { status: 400 });
            }

            const isValid = await bcrypt.compare(currentPassword, dbUser.password);
            if (!isValid) {
                return NextResponse.json({ message: 'Password lama salah' }, { status: 400 });
            }

            if (newPassword.length < 6) {
                return NextResponse.json({ message: 'Password baru minimal 6 karakter' }, { status: 400 });
            }

            updateData.password = await bcrypt.hash(newPassword, 10);
        }

        if (Object.keys(updateData).length === 0) {
            return NextResponse.json({ message: 'Tidak ada yang diubah' }, { status: 400 });
        }

        const updated = await prisma.user.update({
            where: { id: user.id },
            data: updateData,
            select: { id: true, email: true, name: true, avatar: true, coins: true, vipStatus: true }
        });

        return NextResponse.json(updated);
    } catch (error: any) {
        console.error('Profile update error:', error.message);
        return NextResponse.json({ message: 'Gagal memperbarui profil' }, { status: 500 });
    }
}


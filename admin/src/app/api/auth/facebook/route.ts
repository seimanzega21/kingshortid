import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { generateToken } from '@/lib/auth';

// POST /api/auth/facebook
// Receives accessToken from Facebook Login, verifies it, creates/logs in user
export async function POST(request: NextRequest) {
    try {
        const { accessToken } = await request.json();

        if (!accessToken) {
            return NextResponse.json({ message: 'accessToken diperlukan' }, { status: 400 });
        }

        // Verify Facebook access token via Graph API
        const fbResponse = await fetch(
            `https://graph.facebook.com/me?fields=id,name,email,picture.type(large)&access_token=${accessToken}`
        );

        if (!fbResponse.ok) {
            return NextResponse.json({ message: 'Token Facebook tidak valid' }, { status: 401 });
        }

        const fbUser = await fbResponse.json();
        const { id: facebookId, email, name, picture } = fbUser;
        const avatarUrl = picture?.data?.url || null;

        if (!email) {
            return NextResponse.json(
                { message: 'Email tidak ditemukan. Pastikan izin email diberikan di Facebook.' },
                { status: 400 }
            );
        }

        // Check if user already exists (by email or providerId)
        let user = await prisma.user.findFirst({
            where: {
                OR: [
                    { email },
                    { provider: 'facebook', providerId: facebookId },
                ],
            },
        });

        if (user) {
            // Update provider info if user logged in with different method before
            if (user.provider === 'local' || !user.providerId) {
                user = await prisma.user.update({
                    where: { id: user.id },
                    data: {
                        provider: 'facebook',
                        providerId: facebookId,
                        avatar: user.avatar || avatarUrl,
                    },
                });
            }

            if (!user.isActive) {
                return NextResponse.json({ message: 'Akun dinonaktifkan' }, { status: 403 });
            }
        } else {
            // Create new user with registration bonus
            user = await prisma.user.create({
                data: {
                    email,
                    name: name || email.split('@')[0],
                    avatar: avatarUrl,
                    provider: 'facebook',
                    providerId: facebookId,
                    coins: 200,
                },
            });

            // Record registration bonus
            await prisma.coinTransaction.create({
                data: {
                    userId: user.id,
                    type: 'bonus',
                    amount: 200,
                    description: 'Bonus registrasi Facebook',
                    balanceAfter: 200,
                },
            });
        }

        // Generate JWT token
        const token = generateToken({
            id: user.id,
            role: user.role,
        });

        return NextResponse.json({
            token,
            user: {
                id: user.id,
                email: user.email,
                name: user.name,
                avatar: user.avatar,
                coins: user.coins,
                vipStatus: user.vipStatus,
                vipExpiry: user.vipExpiry,
            },
        });
    } catch (error) {
        console.error('Facebook auth error:', error);
        return NextResponse.json({ message: 'Login Facebook gagal' }, { status: 500 });
    }
}

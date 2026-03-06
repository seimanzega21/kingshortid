import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { generateToken } from '@/lib/auth';

// POST /api/auth/google
// Receives idToken from Google Sign-In, verifies it, creates/logs in user
export async function POST(request: NextRequest) {
    try {
        const { idToken } = await request.json();

        if (!idToken) {
            return NextResponse.json({ message: 'idToken diperlukan' }, { status: 400 });
        }

        // Verify Google ID token via Google's tokeninfo endpoint
        const googleResponse = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${idToken}`);

        if (!googleResponse.ok) {
            return NextResponse.json({ message: 'Token Google tidak valid' }, { status: 401 });
        }

        const googleUser = await googleResponse.json();
        const { sub: googleId, email, name, picture } = googleUser;

        if (!email) {
            return NextResponse.json({ message: 'Email tidak ditemukan di akun Google' }, { status: 400 });
        }

        // Check if user already exists (by email or providerId)
        let user = await prisma.user.findFirst({
            where: {
                OR: [
                    { email },
                    { provider: 'google', providerId: googleId },
                ],
            },
        });

        if (user) {
            // Update provider info if user logged in with email before
            if (user.provider === 'local' || !user.providerId) {
                user = await prisma.user.update({
                    where: { id: user.id },
                    data: {
                        provider: 'google',
                        providerId: googleId,
                        avatar: user.avatar || picture || null,
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
                    avatar: picture || null,
                    provider: 'google',
                    providerId: googleId,
                    coins: 200,
                },
            });

            // Record registration bonus
            await prisma.coinTransaction.create({
                data: {
                    userId: user.id,
                    type: 'bonus',
                    amount: 200,
                    description: 'Bonus registrasi Google',
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
        console.error('Google auth error:', error);
        return NextResponse.json({ message: 'Login Google gagal' }, { status: 500 });
    }
}

import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { generateToken } from '@/lib/auth';
import { v4 as uuidv4 } from 'uuid';

// POST /api/auth/guest - Create or reuse guest account by deviceId
export async function POST(request: NextRequest) {
    try {
        let deviceId: string | undefined;
        try {
            const body = await request.json();
            deviceId = body.deviceId;
        } catch {
            // No body or invalid JSON — proceed without deviceId
        }

        // If deviceId provided, try to find existing guest
        if (deviceId) {
            const existingGuest = await prisma.user.findFirst({
                where: { guestId: deviceId, isGuest: true },
            });

            if (existingGuest) {
                // Reuse existing guest account
                const token = generateToken({
                    id: existingGuest.id,
                    role: existingGuest.role,
                });

                return NextResponse.json({
                    token,
                    user: {
                        id: existingGuest.id,
                        email: existingGuest.email,
                        name: existingGuest.name,
                        avatar: existingGuest.avatar,
                        coins: existingGuest.coins,
                        vipStatus: existingGuest.vipStatus,
                        vipExpiry: existingGuest.vipExpiry,
                        isGuest: existingGuest.isGuest,
                        guestId: existingGuest.guestId,
                    },
                });
            }
        }

        // No existing guest found — create new one
        const guestId = deviceId || `guest_${uuidv4()}`;

        const user = await prisma.user.create({
            data: {
                email: `${guestId}@guest.local`,
                name: 'Tamu',
                password: '',
                isGuest: true,
                guestId: guestId,
                coins: 10,
                isActive: true,
            },
        });

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
                isGuest: user.isGuest,
                guestId: user.guestId,
            },
        });
    } catch (error: any) {
        console.error('Guest account error:', error);
        return NextResponse.json(
            { error: 'Failed to create guest account', message: error.message },
            { status: 500 }
        );
    }
}

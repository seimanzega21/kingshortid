import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/watch-party/:code/join - Join a watch party by room code
export async function POST(
    request: NextRequest,
    context: { params: Promise<{ code: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { code } = await context.params;

        // Find watch party by code
        const watchParty = await prisma.watchParty.findUnique({
            where: { roomCode: code },
            include: {
                _count: {
                    select: { participants: { where: { isActive: true } } },
                },
            },
        });

        if (!watchParty) {
            return NextResponse.json(
                { error: 'Watch party not found' },
                { status: 404 }
            );
        }

        if (!watchParty.isActive) {
            return NextResponse.json(
                { error: 'Watch party has ended' },
                { status: 400 }
            );
        }

        // Check if room is full
        if (watchParty._count.participants >= watchParty.maxUsers) {
            return NextResponse.json(
                { error: 'Watch party is full' },
                { status: 400 }
            );
        }

        // Check if already a participant
        const existingParticipant = await prisma.watchPartyParticipant.findUnique({
            where: {
                partyId_userId: {
                    partyId: watchParty.id,
                    userId: user.id,
                },
            },
        });

        if (existingParticipant && existingParticipant.isActive) {
            return NextResponse.json(
                { error: 'Already in this watch party' },
                { status: 400 }
            );
        }

        // Join or rejoin
        if (existingParticipant) {
            await prisma.watchPartyParticipant.update({
                where: { id: existingParticipant.id },
                data: {
                    isActive: true,
                    leftAt: null,
                },
            });
        } else {
            await prisma.watchPartyParticipant.create({
                data: {
                    partyId: watchParty.id,
                    userId: user.id,
                },
            });
        }

        // Get full watch party details
        const fullParty = await prisma.watchParty.findUnique({
            where: { id: watchParty.id },
            include: {
                host: {
                    select: {
                        id: true,
                        name: true,
                        avatar: true,
                    },
                },
                drama: true,
                episode: true,
                participants: {
                    where: { isActive: true },
                    include: {
                        user: {
                            select: {
                                id: true,
                                name: true,
                                avatar: true,
                            },
                        },
                    },
                },
            },
        });

        return NextResponse.json(fullParty);
    } catch (error: any) {
        console.error('Error joining watch party:', error);
        return NextResponse.json(
            { error: 'Failed to join watch party' },
            { status: 500 }
        );
    }
}

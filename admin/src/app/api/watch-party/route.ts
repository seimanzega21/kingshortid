import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// Generate random room code
function generateRoomCode(): string {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
}

// POST /api/watch-party/create - Create a watch party
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { dramaId, episodeId, isPublic, maxUsers } = body;

        if (!dramaId || !episodeId) {
            return NextResponse.json(
                { error: 'dramaId and episodeId are required' },
                { status: 400 }
            );
        }

        // Check if episode exists
        const episode = await prisma.episode.findUnique({
            where: { id: episodeId },
            include: { drama: true },
        });

        if (!episode || episode.dramaId !== dramaId) {
            return NextResponse.json(
                { error: 'Episode not found' },
                { status: 404 }
            );
        }

        // Generate unique room code
        let roomCode = generateRoomCode();
        let exists = await prisma.watchParty.findUnique({ where: { roomCode } });
        while (exists) {
            roomCode = generateRoomCode();
            exists = await prisma.watchParty.findUnique({ where: { roomCode } });
        }

        // Create watch party
        const watchParty = await prisma.watchParty.create({
            data: {
                hostId: user.id,
                dramaId,
                episodeId,
                roomCode,
                isPublic: isPublic !== false,
                maxUsers: maxUsers || 10,
            },
            include: {
                host: {
                    select: {
                        id: true,
                        name: true,
                        avatar: true,
                    },
                },
                drama: {
                    select: {
                        id: true,
                        title: true,
                        cover: true,
                    },
                },
                episode: {
                    select: {
                        id: true,
                        episodeNumber: true,
                        title: true,
                    },
                },
            },
        });

        // Auto-join host as participant
        await prisma.watchPartyParticipant.create({
            data: {
                partyId: watchParty.id,
                userId: user.id,
            },
        });

        return NextResponse.json(watchParty, { status: 201 });
    } catch (error: any) {
        console.error('Error creating watch party:', error);
        return NextResponse.json(
            { error: 'Failed to create watch party' },
            { status: 500 }
        );
    }
}

// GET /api/watch-party/active - List active public watch parties
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');

        const skip = (page - 1) * limit;

        const [parties, total] = await Promise.all([
            prisma.watchParty.findMany({
                where: {
                    isActive: true,
                    isPublic: true,
                },
                orderBy: { createdAt: 'desc' },
                skip,
                take: limit,
                include: {
                    host: {
                        select: {
                            id: true,
                            name: true,
                            avatar: true,
                        },
                    },
                    drama: {
                        select: {
                            id: true,
                            title: true,
                            cover: true,
                        },
                    },
                    episode: {
                        select: {
                            id: true,
                            episodeNumber: true,
                            title: true,
                        },
                    },
                    _count: {
                        select: {
                            participants: { where: { isActive: true } },
                        },
                    },
                },
            }),
            prisma.watchParty.count({
                where: {
                    isActive: true,
                    isPublic: true,
                },
            }),
        ]);

        return NextResponse.json({
            parties,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Error fetching watch parties:', error);
        return NextResponse.json(
            { error: 'Failed to fetch watch parties' },
            { status: 500 }
        );
    }
}

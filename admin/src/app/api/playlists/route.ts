import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/playlists - Get user's playlists or public playlists
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const userId = searchParams.get('userId');
        const isPublic = searchParams.get('public') === 'true';
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');

        const skip = (page - 1) * limit;

        const where: any = {};
        if (userId) where.userId = userId;
        if (isPublic) where.isPublic = true;

        const [playlists, total] = await Promise.all([
            prisma.playlist.findMany({
                where,
                orderBy: { updatedAt: 'desc' },
                skip,
                take: limit,
                include: {
                    user: {
                        select: {
                            id: true,
                            name: true,
                            avatar: true,
                        },
                    },
                    dramas: {
                        take: 4,
                        select: {
                            id: true,
                            title: true,
                            cover: true,
                        },
                    },
                },
            }),
            prisma.playlist.count({ where }),
        ]);

        return NextResponse.json({
            playlists,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Error fetching playlists:', error);
        return NextResponse.json(
            { error: 'Failed to fetch playlists' },
            { status: 500 }
        );
    }
}

// POST /api/playlists - Create a new playlist
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { name, description, isPublic, cover } = body;

        if (!name || name.trim().length === 0) {
            return NextResponse.json(
                { error: 'Playlist name is required' },
                { status: 400 }
            );
        }

        const playlist = await prisma.playlist.create({
            data: {
                userId: user.id,
                name: name.trim(),
                description: description?.trim(),
                isPublic: isPublic || false,
                cover,
            },
            include: {
                user: {
                    select: {
                        id: true,
                        name: true,
                        avatar: true,
                    },
                },
            },
        });

        return NextResponse.json(playlist, { status: 201 });
    } catch (error: any) {
        console.error('Error creating playlist:', error);
        return NextResponse.json(
            { error: 'Failed to create playlist' },
            { status: 500 }
        );
    }
}

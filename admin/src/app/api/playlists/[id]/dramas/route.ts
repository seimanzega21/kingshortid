import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/playlists/:id/dramas - Add drama to playlist
export async function POST(
    request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { id } = await context.params;
        const body = await request.json();
        const { dramaId } = body;

        if (!dramaId) {
            return NextResponse.json(
                { error: 'dramaId is required' },
                { status: 400 }
            );
        }

        // Check playlist ownership
        const playlist = await prisma.playlist.findUnique({
            where: { id },
            include: { dramas: true },
        });

        if (!playlist) {
            return NextResponse.json(
                { error: 'Playlist not found' },
                { status: 404 }
            );
        }

        if (playlist.userId !== user.id) {
            return NextResponse.json(
                { error: 'You can only edit your own playlists' },
                { status: 403 }
            );
        }

        // Check if drama exists
        const drama = await prisma.drama.findUnique({
            where: { id: dramaId },
        });

        if (!drama) {
            return NextResponse.json(
                { error: 'Drama not found' },
                { status: 404 }
            );
        }

        // Check if already in playlist
        const alreadyAdded = playlist.dramas.some((d) => d.id === dramaId);
        if (alreadyAdded) {
            return NextResponse.json(
                { error: 'Drama already in playlist' },
                { status: 400 }
            );
        }

        // Add drama to playlist
        await prisma.playlist.update({
            where: { id },
            data: {
                dramas: {
                    connect: { id: dramaId },
                },
                itemCount: {
                    increment: 1,
                },
            },
        });

        return NextResponse.json({ message: 'Drama added to playlist' });
    } catch (error: any) {
        console.error('Error adding drama to playlist:', error);
        return NextResponse.json(
            { error: 'Failed to add drama to playlist' },
            { status: 500 }
        );
    }
}

// DELETE /api/playlists/:id/dramas - Remove drama from playlist  
export async function DELETE(
    request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { id } = await context.params;
        const { searchParams } = new URL(request.url);
        const dramaId = searchParams.get('dramaId');

        if (!dramaId) {
            return NextResponse.json(
                { error: 'dramaId is required' },
                { status: 400 }
            );
        }

        // Check playlist ownership
        const playlist = await prisma.playlist.findUnique({
            where: { id },
        });

        if (!playlist) {
            return NextResponse.json(
                { error: 'Playlist not found' },
                { status: 404 }
            );
        }

        if (playlist.userId !== user.id) {
            return NextResponse.json(
                { error: 'You can only edit your own playlists' },
                { status: 403 }
            );
        }

        // Remove drama from playlist
        await prisma.playlist.update({
            where: { id },
            data: {
                dramas: {
                    disconnect: { id: dramaId },
                },
                itemCount: {
                    decrement: 1,
                },
            },
        });

        return NextResponse.json({ message: 'Drama removed from playlist' });
    } catch (error: any) {
        console.error('Error removing drama from playlist:', error);
        return NextResponse.json(
            { error: 'Failed to remove drama from playlist' },
            { status: 500 }
        );
    }
}

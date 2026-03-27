import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/dramas/[id]/episodes — List all episodes for a drama
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        // Use raw query for reliable episode fetching
        const episodes: any[] = await prisma.$queryRaw`
            SELECT id, "episodeNumber", title, description, thumbnail,
                   "videoUrl", duration, views, "isVip", "coinPrice",
                   "isActive", "createdAt"
            FROM "Episode" 
            WHERE "dramaId" = ${id}
            ORDER BY "episodeNumber" ASC
        `;

        return NextResponse.json({ episodes, total: episodes.length, _version: 'raw_v2' });
    } catch (error) {
        console.error('Get episodes error:', error);
        return NextResponse.json(
            { message: 'Failed to get episodes' },
            { status: 500 }
        );
    }
}

// POST /api/dramas/[id]/episodes — Create episode
export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id: dramaId } = await params;
        const body = await request.json();

        // Get next episode number
        const lastEpisode = await prisma.episode.findFirst({
            where: { dramaId },
            orderBy: { episodeNumber: 'desc' },
        });
        const nextNumber = (lastEpisode?.episodeNumber || 0) + 1;

        const episode = await prisma.episode.create({
            data: {
                dramaId,
                episodeNumber: body.episodeNumber || nextNumber,
                title: body.title || `Episode ${body.episodeNumber || nextNumber}`,
                description: body.description || null,
                thumbnail: body.thumbnail || null,
                videoUrl: body.videoUrl || '',
                duration: body.duration || 0,
                isVip: body.isVip || false,
                coinPrice: body.coinPrice || 0,
            },
        });

        // Update drama episode count
        await prisma.drama.update({
            where: { id: dramaId },
            data: { totalEpisodes: { increment: 1 } },
        });

        return NextResponse.json(episode, { status: 201 });
    } catch (error: any) {
        console.error('Create episode error:', error);
        return NextResponse.json(
            { message: error.message || 'Failed to create episode' },
            { status: 500 }
        );
    }
}

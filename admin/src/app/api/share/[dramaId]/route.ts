import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/share/[dramaId] - Get drama info for deep linking
export async function GET(
    req: NextRequest,
    context: { params: Promise<{ dramaId: string }> }
) {
    try {
        const { dramaId } = await context.params;

        const drama = await prisma.drama.findUnique({
            where: { id: dramaId, isActive: true },
            include: {
                episodes: {
                    where: { isActive: true },
                    orderBy: { episodeNumber: 'asc' },
                    take: 1,
                },
            },
        });

        if (!drama) {
            return NextResponse.json({ error: 'Drama not found' }, { status: 404 });
        }

        // Increment view count for tracking
        await prisma.drama.update({
            where: { id: dramaId },
            data: { views: { increment: 1 } },
        });

        // Return data for mobile deep link handling
        return NextResponse.json({
            id: drama.id,
            title: drama.title,
            description: drama.description,
            cover: drama.cover,
            banner: drama.banner,
            genres: drama.genres,
            rating: drama.rating,
            totalEpisodes: drama.totalEpisodes,
            firstEpisodeId: drama.episodes[0]?.id,
            shareUrl: `https://kingshort.app/drama/${dramaId}`,
        });
    } catch (error) {
        console.error('Share data error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

// POST /api/share/[dramaId]/track - Track share events
export async function POST(
    req: NextRequest,
    context: { params: Promise<{ dramaId: string }> }
) {
    try {
        const { dramaId } = await context.params;
        const { platform, userId } = await req.json();

        // Track share event for analytics
        console.log(`Share tracked: Drama ${dramaId} shared on ${platform} by user ${userId || 'guest'}`);

        // For now, just return success
        return NextResponse.json({ success: true });
    } catch (error) {
        console.error('Share tracking error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

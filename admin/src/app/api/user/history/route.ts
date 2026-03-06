import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/user/history
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const { searchParams } = new URL(request.url);
        const limit = parseInt(searchParams.get('limit') || '20');

        const [history, total] = await Promise.all([
            prisma.watchHistory.findMany({
                where: { userId: user.id },
                orderBy: { watchedAt: 'desc' },
                take: limit,
                include: {
                    drama: {
                        select: { id: true, title: true, cover: true }
                    }
                }
            }),
            prisma.watchHistory.count({ where: { userId: user.id } })
        ]);

        return NextResponse.json({ history, total });
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

// POST /api/user/history (Update Progress)
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const { dramaId, episodeNumber, progress, episodeId } = await request.json();

        if (!dramaId || !episodeNumber) {
            return NextResponse.json({ message: 'dramaId and episodeNumber required' }, { status: 400 });
        }

        // Resolve episodeId: use provided one or look up by dramaId + episodeNumber
        let resolvedEpisodeId = episodeId;
        if (!resolvedEpisodeId) {
            const episode = await prisma.episode.findUnique({
                where: { dramaId_episodeNumber: { dramaId, episodeNumber } },
                select: { id: true }
            });
            if (!episode) {
                return NextResponse.json({ message: 'Episode not found' }, { status: 404 });
            }
            resolvedEpisodeId = episode.id;
        }

        await prisma.watchHistory.upsert({
            where: {
                userId_dramaId_episodeId: {
                    userId: user.id,
                    dramaId,
                    episodeId: resolvedEpisodeId
                }
            },
            update: {
                progress,
                watchedAt: new Date()
            },
            create: {
                userId: user.id,
                dramaId,
                episodeId: resolvedEpisodeId,
                episodeNumber,
                progress,
                watchedAt: new Date()
            }
        });

        return NextResponse.json({ success: true });
    } catch (error: any) {
        console.error('Watch history error:', error.message, error.code);
        return NextResponse.json({ message: 'Error', detail: error.message }, { status: 500 });
    }
}

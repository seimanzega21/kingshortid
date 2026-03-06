import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/episodes - List episodes with filters
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');
        const dramaId = searchParams.get('dramaId');
        const isVip = searchParams.get('isVip');
        const search = searchParams.get('q');

        const where: any = {};

        if (dramaId) where.dramaId = dramaId;
        if (isVip === 'true') where.isVip = true;
        if (isVip === 'false') where.isVip = false;
        if (search) {
            where.OR = [
                { title: { contains: search, mode: 'insensitive' } },
                { drama: { title: { contains: search, mode: 'insensitive' } } },
            ];
        }

        const [episodes, total] = await Promise.all([
            prisma.episode.findMany({
                where,
                orderBy: [{ createdAt: 'desc' }],
                take: limit,
                skip: (page - 1) * limit,
                include: {
                    drama: {
                        select: { id: true, title: true, cover: true }
                    }
                }
            }),
            prisma.episode.count({ where }),
        ]);

        return NextResponse.json({
            episodes,
            total,
            page,
            pages: Math.ceil(total / limit),
        });
    } catch (error) {
        console.error('Get episodes error:', error);
        return NextResponse.json(
            { message: 'Failed to get episodes' },
            { status: 500 }
        );
    }
}

// POST /api/episodes - Create episode
export async function POST(request: NextRequest) {
    try {
        const data = await request.json();

        if (!data.dramaId) {
            return NextResponse.json({ message: 'Drama ID is required' }, { status: 400 });
        }

        if (!data.title) {
            return NextResponse.json({ message: 'Episode title is required' }, { status: 400 });
        }

        // Get next episode number
        const lastEpisode = await prisma.episode.findFirst({
            where: { dramaId: data.dramaId },
            orderBy: { episodeNumber: 'desc' }
        });
        const nextNumber = (lastEpisode?.episodeNumber || 0) + 1;

        const episode = await prisma.episode.create({
            data: {
                dramaId: data.dramaId,
                episodeNumber: data.episodeNumber || nextNumber,
                title: data.title,
                description: data.description || null,
                thumbnail: data.thumbnail || null,
                videoUrl: data.videoUrl || null,
                duration: data.duration || 0,
                isVip: data.isVip || false,
                coinPrice: data.coinPrice || 0,
            },
            include: {
                drama: { select: { title: true } }
            }
        });

        // Update drama episode count
        await prisma.drama.update({
            where: { id: data.dramaId },
            data: { totalEpisodes: { increment: 1 } }
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

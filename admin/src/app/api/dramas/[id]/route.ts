import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/dramas/[id]
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        const drama = await prisma.drama.findUnique({
            where: { id },
            include: {
                _count: {
                    select: {
                        episodes: true,
                        favorites: true,
                        watchlist: true,
                        comments: true,
                        reviews: true,
                    },
                },
                episodes: {
                    orderBy: { episodeNumber: 'asc' },
                    select: {
                        id: true,
                        episodeNumber: true,
                        title: true,
                        videoUrl: true,
                        duration: true,
                        views: true,
                        isVip: true,
                        isActive: true,
                        createdAt: true,
                    },
                },
            },
        });

        if (!drama) {
            return NextResponse.json(
                { message: 'Drama not found' },
                { status: 404 }
            );
        }

        return NextResponse.json(drama);
    } catch (error) {
        console.error('Get drama error:', error);
        return NextResponse.json(
            { message: 'Failed to get drama' },
            { status: 500 }
        );
    }
}

// PATCH /api/dramas/[id]
export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const body = await request.json();

        const allowedFields = [
            'title', 'description', 'cover', 'banner', 'genres', 'tagList',
            'status', 'isVip', 'isFeatured', 'isActive', 'ageRating',
            'director', 'cast', 'country', 'language', 'totalEpisodes',
            'rating', 'views',
        ];

        const updateData: any = {};
        for (const field of allowedFields) {
            if (body[field] !== undefined) {
                updateData[field] = body[field];
            }
        }

        const drama = await prisma.drama.update({
            where: { id },
            data: updateData,
        });

        return NextResponse.json(drama);
    } catch (error: any) {
        console.error('Update drama error:', error);
        if (error.code === 'P2025') {
            return NextResponse.json(
                { message: 'Drama not found' },
                { status: 404 }
            );
        }
        return NextResponse.json(
            { message: 'Failed to update drama' },
            { status: 500 }
        );
    }
}

// DELETE /api/dramas/[id]
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        await prisma.drama.delete({ where: { id } });

        return NextResponse.json({ message: 'Drama deleted' });
    } catch (error: any) {
        console.error('Delete drama error:', error);
        if (error.code === 'P2025') {
            return NextResponse.json(
                { message: 'Drama not found' },
                { status: 404 }
            );
        }
        return NextResponse.json(
            { message: 'Failed to delete drama' },
            { status: 500 }
        );
    }
}

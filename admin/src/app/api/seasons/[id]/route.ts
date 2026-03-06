import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

/**
 * GET /api/seasons/[id]
 * Get season details by ID
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        const season = await prisma.season.findUnique({
            where: { id },
            include: {
                drama: {
                    select: {
                        id: true,
                        title: true,
                        cover: true,
                    },
                },
                episodes: {
                    orderBy: {
                        episodeNumber: 'asc',
                    },
                    select: {
                        id: true,
                        episodeNumber: true,
                        title: true,
                        description: true,
                        thumbnail: true,
                        duration: true,
                        isVip: true,
                        coinPrice: true,
                        views: true,
                        releaseDate: true,
                    },
                },
                _count: {
                    select: { episodes: true },
                },
            },
        });

        if (!season) {
            return NextResponse.json(
                { error: 'Season not found' },
                { status: 404 }
            );
        }

        return NextResponse.json({
            ...season,
            episodeCount: season._count.episodes,
        });
    } catch (error: any) {
        console.error('Error fetching season:', error);
        return NextResponse.json(
            { error: 'Failed to fetch season' },
            { status: 500 }
        );
    }
}

/**
 * PUT /api/seasons/[id]
 * Update season details (Admin only)
 */
export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const body = await request.json();
        const { title, description, poster, trailer, releaseDate } = body;

        const season = await prisma.season.update({
            where: { id },
            data: {
                title,
                description,
                poster,
                trailer,
                releaseDate: releaseDate ? new Date(releaseDate) : undefined,
            },
        });

        return NextResponse.json(season);
    } catch (error: any) {
        console.error('Error updating season:', error);
        return NextResponse.json(
            { error: 'Failed to update season' },
            { status: 500 }
        );
    }
}

/**
 * DELETE /api/seasons/[id]
 * Delete a season (Admin only)
 */
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        await prisma.season.delete({
            where: { id },
        });

        return NextResponse.json({ message: 'Season deleted successfully' });
    } catch (error: any) {
        console.error('Error deleting season:', error);
        return NextResponse.json(
            { error: 'Failed to delete season' },
            { status: 500 }
        );
    }
}

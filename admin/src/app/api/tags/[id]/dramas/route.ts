import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

/**
 * GET /api/tags/[id]/dramas
 * Get all dramas associated with a specific tag
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { searchParams } = new URL(request.url);

        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');
        const skip = (page - 1) * limit;

        // Check if tag exists
        const tag = await prisma.tag.findUnique({
            where: { id },
            select: { id: true, name: true, type: true },
        });

        if (!tag) {
            return NextResponse.json(
                { error: 'Tag not found' },
                { status: 404 }
            );
        }

        // Get dramas with this tag
        const [dramas, total] = await Promise.all([
            prisma.drama.findMany({
                where: {
                    tags: {
                        some: { id },
                    },
                    isActive: true,
                },
                orderBy: {
                    views: 'desc',
                },
                skip,
                take: limit,
                select: {
                    id: true,
                    title: true,
                    description: true,
                    cover: true,
                    banner: true,
                    genres: true,
                    rating: true,
                    views: true,
                    totalEpisodes: true,
                    isVip: true,
                    isFeatured: true,
                    releaseDate: true,
                    tags: {
                        select: {
                            id: true,
                            name: true,
                            slug: true,
                            type: true,
                            color: true,
                        },
                    },
                },
            }),
            prisma.drama.count({
                where: {
                    tags: {
                        some: { id },
                    },
                    isActive: true,
                },
            }),
        ]);

        return NextResponse.json({
            tag,
            dramas,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Error fetching dramas by tag:', error);
        return NextResponse.json(
            { error: 'Failed to fetch dramas' },
            { status: 500 }
        );
    }
}

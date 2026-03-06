import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/dramas — List dramas from Supabase
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');
        const search = searchParams.get('q');
        const includeInactive = searchParams.get('includeInactive') === 'true';

        const where: any = {};

        if (!includeInactive) {
            where.isActive = true;
        }

        if (search) {
            where.OR = [
                { title: { contains: search, mode: 'insensitive' } },
                { description: { contains: search, mode: 'insensitive' } },
            ];
        }

        const [dramas, total] = await Promise.all([
            prisma.drama.findMany({
                where,
                orderBy: { createdAt: 'desc' },
                take: limit,
                skip: (page - 1) * limit,
                select: {
                    id: true,
                    title: true,
                    cover: true,
                    genres: true,
                    totalEpisodes: true,
                    views: true,
                    rating: true,
                    status: true,
                    isActive: true,
                    isFeatured: true,
                    isVip: true,
                    createdAt: true,
                    updatedAt: true,
                    _count: {
                        select: { episodes: true },
                    },
                },
            }),
            prisma.drama.count({ where }),
        ]);

        return NextResponse.json({
            dramas: dramas.map(d => ({
                ...d,
                episodeCount: d._count.episodes,
                _count: undefined,
            })),
            total,
            page,
            pages: Math.ceil(total / limit),
        });
    } catch (error) {
        console.error('Get dramas error:', error);
        return NextResponse.json(
            { message: 'Failed to get dramas' },
            { status: 500 }
        );
    }
}

// POST /api/dramas — Create drama
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        const drama = await prisma.drama.create({
            data: {
                title: body.title,
                description: body.description || '',
                cover: body.cover || '',
                banner: body.banner || null,
                genres: body.genres || [],
                tagList: body.tagList || [],
                status: body.status || 'ongoing',
                isVip: body.isVip || false,
                isFeatured: body.isFeatured || false,
                isActive: body.isActive !== undefined ? body.isActive : true,
                ageRating: body.ageRating || 'all',
                director: body.director || null,
                cast: body.cast || [],
                country: body.country || 'China',
                language: body.language || 'Mandarin',
            },
        });

        return NextResponse.json(drama, { status: 201 });
    } catch (error: any) {
        console.error('Create drama error:', error);
        return NextResponse.json(
            { message: error.message || 'Failed to create drama' },
            { status: 500 }
        );
    }
}

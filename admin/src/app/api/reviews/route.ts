import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/reviews - Get reviews for a drama
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const dramaId = searchParams.get('dramaId');
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '10');
        const sortBy = searchParams.get('sortBy') || 'helpful'; // helpful, latest, rating

        if (!dramaId) {
            return NextResponse.json(
                { error: 'dramaId is required' },
                { status: 400 }
            );
        }

        const skip = (page - 1) * limit;

        // Build orderBy clause
        let orderBy: any = {};
        switch (sortBy) {
            case 'latest':
                orderBy = { createdAt: 'desc' };
                break;
            case 'rating':
                orderBy = { rating: 'desc' };
                break;
            default: // helpful
                orderBy = { helpfulCount: 'desc' };
        }

        const [reviews, total, stats] = await Promise.all([
            prisma.review.findMany({
                where: { dramaId, isReported: false },
                orderBy,
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
                },
            }),
            prisma.review.count({ where: { dramaId, isReported: false } }),
            prisma.review.aggregate({
                where: { dramaId, isReported: false },
                _avg: { rating: true },
                _count: { rating: true },
            }),
        ]);

        return NextResponse.json({
            reviews,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
            stats: {
                averageRating: stats._avg.rating || 0,
                totalReviews: stats._count.rating || 0,
            },
        });
    } catch (error: any) {
        console.error('Error fetching reviews:', error);
        return NextResponse.json(
            { error: 'Failed to fetch reviews' },
            { status: 500 }
        );
    }
}

// POST /api/reviews - Create or update a review
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { dramaId, rating, title, content, isSpoiler } = body;

        if (!dramaId || !rating || !title || !content) {
            return NextResponse.json(
                { error: 'dramaId, rating, title, and content are required' },
                { status: 400 }
            );
        }

        if (rating < 1 || rating > 5) {
            return NextResponse.json(
                { error: 'Rating must be between 1 and 5' },
                { status: 400 }
            );
        }

        if (title.length > 100) {
            return NextResponse.json(
                { error: 'Title is too long (max 100 characters)' },
                { status: 400 }
            );
        }

        if (content.length > 1000) {
            return NextResponse.json(
                { error: 'Review is too long (max 1000 characters)' },
                { status: 400 }
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

        // Check if user already reviewed this drama
        const existingReview = await prisma.review.findUnique({
            where: {
                userId_dramaId: {
                    userId: user.id,
                    dramaId,
                },
            },
        });

        let review;
        if (existingReview) {
            // Update existing review
            review = await prisma.review.update({
                where: { id: existingReview.id },
                data: {
                    rating,
                    title: title.trim(),
                    content: content.trim(),
                    isSpoiler: isSpoiler || false,
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
        } else {
            // Create new review
            review = await prisma.review.create({
                data: {
                    userId: user.id,
                    dramaId,
                    rating,
                    title: title.trim(),
                    content: content.trim(),
                    isSpoiler: isSpoiler || false,
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
        }

        // Update drama's average rating and review count
        const reviewStats = await prisma.review.aggregate({
            where: { dramaId, isReported: false },
            _avg: { rating: true },
            _count: { rating: true },
        });

        await prisma.drama.update({
            where: { id: dramaId },
            data: {
                averageRating: reviewStats._avg.rating || 0,
                reviewCount: reviewStats._count.rating || 0,
            },
        });

        return NextResponse.json(review, { status: existingReview ? 200 : 201 });
    } catch (error: any) {
        console.error('Error creating review:', error);
        return NextResponse.json(
            { error: 'Failed to create review' },
            { status: 500 }
        );
    }
}

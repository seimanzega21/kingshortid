import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/reviews/:id/helpful - Mark review as helpful
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

        // Check if review exists
        const review = await prisma.review.findUnique({
            where: { id },
        });

        if (!review) {
            return NextResponse.json(
                { error: 'Review not found' },
                { status: 404 }
            );
        }

        // Check if user already marked this review as helpful
        const existingHelpful = await prisma.reviewHelpful.findUnique({
            where: {
                userId_reviewId: {
                    userId: user.id,
                    reviewId: id,
                },
            },
        });

        if (existingHelpful) {
            // Remove helpful mark
            await prisma.$transaction([
                prisma.reviewHelpful.delete({
                    where: { id: existingHelpful.id },
                }),
                prisma.review.update({
                    where: { id },
                    data: {
                        helpfulCount: {
                            decrement: 1,
                        },
                    },
                }),
            ]);

            return NextResponse.json({
                helpful: false,
                helpfulCount: review.helpfulCount - 1,
            });
        } else {
            // Mark as helpful
            await prisma.$transaction([
                prisma.reviewHelpful.create({
                    data: {
                        userId: user.id,
                        reviewId: id,
                    },
                }),
                prisma.review.update({
                    where: { id },
                    data: {
                        helpfulCount: {
                            increment: 1,
                        },
                    },
                }),
            ]);

            return NextResponse.json({
                helpful: true,
                helpfulCount: review.helpfulCount + 1,
            });
        }
    } catch (error: any) {
        console.error('Error marking review as helpful:', error);
        return NextResponse.json(
            { error: 'Failed to mark review as helpful' },
            { status: 500 }
        );
    }
}

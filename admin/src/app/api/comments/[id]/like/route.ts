import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/comments/:id/like - Like/Unlike a comment
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

        // Check if comment exists
        const comment = await prisma.comment.findUnique({
            where: { id },
        });

        if (!comment) {
            return NextResponse.json(
                { error: 'Comment not found' },
                { status: 404 }
            );
        }

        // Check if user already liked this comment
        const existingLike = await prisma.commentLike.findUnique({
            where: {
                userId_commentId: {
                    userId: user.id,
                    commentId: id,
                },
            },
        });

        if (existingLike) {
            // Unlike: Remove the like
            await prisma.$transaction([
                prisma.commentLike.delete({
                    where: { id: existingLike.id },
                }),
                prisma.comment.update({
                    where: { id },
                    data: {
                        likeCount: {
                            decrement: 1,
                        },
                    },
                }),
            ]);

            return NextResponse.json({
                liked: false,
                likeCount: comment.likeCount - 1,
            });
        } else {
            // Like: Add the like
            await prisma.$transaction([
                prisma.commentLike.create({
                    data: {
                        userId: user.id,
                        commentId: id,
                    },
                }),
                prisma.comment.update({
                    where: { id },
                    data: {
                        likeCount: {
                            increment: 1,
                        },
                    },
                }),
            ]);

            return NextResponse.json({
                liked: true,
                likeCount: comment.likeCount + 1,
            });
        }
    } catch (error: any) {
        console.error('Error liking comment:', error);
        return NextResponse.json(
            { error: 'Failed to like comment' },
            { status: 500 }
        );
    }
}

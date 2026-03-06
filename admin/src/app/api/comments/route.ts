import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/comments - Get comments for a drama or episode
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const dramaId = searchParams.get('dramaId');
        const episodeId = searchParams.get('episodeId');
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');
        const sortBy = searchParams.get('sortBy') || 'latest'; // latest, top, oldest

        if (!dramaId && !episodeId) {
            return NextResponse.json(
                { error: 'dramaId or episodeId is required' },
                { status: 400 }
            );
        }

        const skip = (page - 1) * limit;

        // Build where clause
        const where: any = {
            isDeleted: false,
            parentId: null, // Only top-level comments
        };

        if (dramaId) where.dramaId = dramaId;
        if (episodeId) where.episodeId = episodeId;

        // Build orderBy clause
        let orderBy: any = {};
        switch (sortBy) {
            case 'top':
                orderBy = { likeCount: 'desc' };
                break;
            case 'oldest':
                orderBy = { createdAt: 'asc' };
                break;
            default: // latest
                orderBy = { createdAt: 'desc' };
        }

        const [comments, total] = await Promise.all([
            prisma.comment.findMany({
                where,
                orderBy,
                skip,
                take: limit,
                include: {
                    user: {
                        select: {
                            id: true,
                            name: true,
                            avatar: true,
                            role: true,
                        },
                    },
                    replies: {
                        where: { isDeleted: false },
                        take: 3, // Show first 3 replies
                        orderBy: { createdAt: 'asc' },
                        include: {
                            user: {
                                select: {
                                    id: true,
                                    name: true,
                                    avatar: true,
                                    role: true,
                                },
                            },
                        },
                    },
                    _count: {
                        select: {
                            replies: { where: { isDeleted: false } },
                        },
                    },
                },
            }),
            prisma.comment.count({ where }),
        ]);

        return NextResponse.json({
            comments,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Error fetching comments:', error);
        return NextResponse.json(
            { error: 'Failed to fetch comments' },
            { status: 500 }
        );
    }
}

// POST /api/comments - Create a new comment
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { content, dramaId, episodeId, parentId } = body;

        if (!content || content.trim().length === 0) {
            return NextResponse.json(
                { error: 'Content is required' },
                { status: 400 }
            );
        }

        if (!dramaId && !episodeId) {
            return NextResponse.json(
                { error: 'dramaId or episodeId is required' },
                { status: 400 }
            );
        }

        // Check if content is too long (max 500 characters)
        if (content.length > 500) {
            return NextResponse.json(
                { error: 'Comment is too long (max 500 characters)' },
                { status: 400 }
            );
        }

        // If replying, verify parent comment exists
        if (parentId) {
            const parentComment = await prisma.comment.findUnique({
                where: { id: parentId },
            });

            if (!parentComment) {
                return NextResponse.json(
                    { error: 'Parent comment not found' },
                    { status: 404 }
                );
            }

            // Prevent nesting more than 3 levels
            if (parentComment.parentId) {
                const grandParent = await prisma.comment.findUnique({
                    where: { id: parentComment.parentId },
                });
                if (grandParent?.parentId) {
                    return NextResponse.json(
                        { error: 'Maximum nesting level reached' },
                        { status: 400 }
                    );
                }
            }
        }

        const comment = await prisma.comment.create({
            data: {
                content: content.trim(),
                userId: user.id,
                dramaId: dramaId || undefined,
                episodeId: episodeId || undefined,
                parentId: parentId || undefined,
            },
            include: {
                user: {
                    select: {
                        id: true,
                        name: true,
                        avatar: true,
                        role: true,
                    },
                },
            },
        });

        return NextResponse.json(comment, { status: 201 });
    } catch (error: any) {
        console.error('Error creating comment:', error);
        return NextResponse.json(
            { error: 'Failed to create comment' },
            { status: 500 }
        );
    }
}

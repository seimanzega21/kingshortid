import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/social/followers - Get user's followers
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { searchParams } = new URL(request.url);
        const userId = searchParams.get('userId') || user.id;
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');

        const skip = (page - 1) * limit;

        const [followers, total] = await Promise.all([
            prisma.follow.findMany({
                where: { followingId: userId },
                orderBy: { createdAt: 'desc' },
                skip,
                take: limit,
                include: {
                    follower: {
                        select: {
                            id: true,
                            name: true,
                            avatar: true,
                            bio: true,
                            followerCount: true,
                            followingCount: true,
                        },
                    },
                },
            }),
            prisma.follow.count({ where: { followingId: userId } }),
        ]);

        return NextResponse.json({
            followers: followers.map((f) => f.follower),
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Error fetching followers:', error);
        return NextResponse.json(
            { error: 'Failed to fetch followers' },
            { status: 500 }
        );
    }
}

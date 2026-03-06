import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/social/following - Get user's following list
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

        const [following, total] = await Promise.all([
            prisma.follow.findMany({
                where: { followerId: userId },
                orderBy: { createdAt: 'desc' },
                skip,
                take: limit,
                include: {
                    following: {
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
            prisma.follow.count({ where: { followerId: userId } }),
        ]);

        return NextResponse.json({
            following: following.map((f) => f.following),
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Error fetching following:', error);
        return NextResponse.json(
            { error: 'Failed to fetch following' },
            { status: 500 }
        );
    }
}

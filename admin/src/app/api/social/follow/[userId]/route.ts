import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/social/follow/:userId - Follow a user
export async function POST(
    request: NextRequest,
    context: { params: Promise<{ userId: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { userId } = await context.params;

        // Can't follow yourself
        if (userId === user.id) {
            return NextResponse.json(
                { error: 'You cannot follow yourself' },
                { status: 400 }
            );
        }

        // Check if target user exists
        const targetUser = await prisma.user.findUnique({
            where: { id: userId },
        });

        if (!targetUser) {
            return NextResponse.json(
                { error: 'User not found' },
                { status: 404 }
            );
        }

        // Check if already following
        const existingFollow = await prisma.follow.findUnique({
            where: {
                followerId_followingId: {
                    followerId: user.id,
                    followingId: userId,
                },
            },
        });

        if (existingFollow) {
            return NextResponse.json(
                { error: 'Already following this user' },
                { status: 400 }
            );
        }

        // Create follow relationship and update counts
        await prisma.$transaction([
            prisma.follow.create({
                data: {
                    followerId: user.id,
                    followingId: userId,
                },
            }),
            prisma.user.update({
                where: { id: user.id },
                data: {
                    followingCount: {
                        increment: 1,
                    },
                },
            }),
            prisma.user.update({
                where: { id: userId },
                data: {
                    followerCount: {
                        increment: 1,
                    },
                },
            }),
        ]);

        return NextResponse.json({
            message: 'User followed successfully',
            following: true,
        });
    } catch (error: any) {
        console.error('Error following user:', error);
        return NextResponse.json(
            { error: 'Failed to follow user' },
            { status: 500 }
        );
    }
}

// DELETE /api/social/follow/:userId - Unfollow a user
export async function DELETE(
    request: NextRequest,
    context: { params: Promise<{ userId: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { userId } = await context.params;

        // Find follow relationship
        const follow = await prisma.follow.findUnique({
            where: {
                followerId_followingId: {
                    followerId: user.id,
                    followingId: userId,
                },
            },
        });

        if (!follow) {
            return NextResponse.json(
                { error: 'Not following this user' },
                { status: 400 }
            );
        }

        // Delete follow relationship and update counts
        await prisma.$transaction([
            prisma.follow.delete({
                where: { id: follow.id },
            }),
            prisma.user.update({
                where: { id: user.id },
                data: {
                    followingCount: {
                        decrement: 1,
                    },
                },
            }),
            prisma.user.update({
                where: { id: userId },
                data: {
                    followerCount: {
                        decrement: 1,
                    },
                },
            }),
        ]);

        return NextResponse.json({
            message: 'User unfollowed successfully',
            following: false,
        });
    } catch (error: any) {
        console.error('Error unfollowing user:', error);
        return NextResponse.json(
            { error: 'Failed to unfollow user' },
            { status: 500 }
        );
    }
}

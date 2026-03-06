import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/users/[id] — Get user detail from Supabase
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const user = await prisma.user.findUnique({
            where: { id },
            include: {
                _count: {
                    select: {
                        watchHistory: true,
                        favorites: true,
                        watchlist: true,
                        comments: true,
                        reviews: true,
                        coinTransactions: true,
                    },
                },
                watchHistory: {
                    orderBy: { watchedAt: 'desc' },
                    take: 5,
                    select: {
                        dramaId: true,
                        episodeNumber: true,
                        progress: true,
                        watchedAt: true,
                        drama: {
                            select: { title: true, cover: true },
                        },
                    },
                },
            },
        });

        if (!user) {
            return NextResponse.json(
                { message: 'User not found' },
                { status: 404 }
            );
        }

        return NextResponse.json({
            ...user,
            recentHistory: user.watchHistory,
            watchHistory: undefined,
        });
    } catch (error) {
        console.error('Get user error:', error);
        return NextResponse.json(
            { message: 'Failed to fetch user' },
            { status: 500 }
        );
    }
}

// PATCH /api/users/[id] — Update user
export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const body = await request.json();

        // Only allow certain fields to be updated by admin
        const allowedFields = ['name', 'role', 'isActive', 'vipStatus', 'coins'];
        const updateData: any = {};
        for (const field of allowedFields) {
            if (body[field] !== undefined) {
                updateData[field] = body[field];
            }
        }

        const user = await prisma.user.update({
            where: { id },
            data: updateData,
        });

        return NextResponse.json(user);
    } catch (error: any) {
        console.error('Update user error:', error);
        if (error.code === 'P2025') {
            return NextResponse.json(
                { message: 'User not found' },
                { status: 404 }
            );
        }
        return NextResponse.json(
            { message: 'Failed to update user' },
            { status: 500 }
        );
    }
}

// DELETE /api/users/[id] — Delete user
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        await prisma.user.delete({ where: { id } });

        return NextResponse.json({ message: 'User deleted' });
    } catch (error: any) {
        console.error('Delete user error:', error);
        if (error.code === 'P2025') {
            return NextResponse.json(
                { message: 'User not found' },
                { status: 404 }
            );
        }
        return NextResponse.json(
            { message: 'Failed to delete user' },
            { status: 500 }
        );
    }
}

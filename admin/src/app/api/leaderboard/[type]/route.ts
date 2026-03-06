import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyToken } from '@/lib/auth';

// GET /api/leaderboard/:type - Get leaderboard by type
export async function GET(
    request: NextRequest,
    context: { params: Promise<{ type: string }> }
) {
    try {
        const { type } = await context.params;
        const { searchParams } = new URL(request.url);
        const period = searchParams.get('period') || 'all_time'; // all_time, monthly, weekly
        const limit = parseInt(searchParams.get('limit') || '100');

        let orderBy: any = {};
        let select: any = {
            id: true,
            name: true,
            avatar: true,
        };

        // Determine what to query based on type
        switch (type) {
            case 'coins':
                orderBy = { coins: 'desc' };
                select.coins = true;
                break;
            case 'achievements':
                orderBy = { achievements: { _count: 'desc' } };
                select._count = { select: { achievements: true } };
                break;
            case 'watch_time':
                orderBy = { totalWatchTime: 'desc' };
                select.totalWatchTime = true;
                break;
            case 'followers':
                orderBy = { followerCount: 'desc' };
                select.followerCount = true;
                break;
            default:
                return NextResponse.json(
                    { error: 'Invalid leaderboard type' },
                    { status: 400 }
                );
        }

        // For time-based filters, we'd need additional logic
        // For now, we'll just get all-time leaderboard
        const users = await prisma.user.findMany({
            where: { isActive: true },
            orderBy,
            take: limit,
            select,
        });

        return NextResponse.json({
            leaderboard: users.map((user, index) => ({
                rank: index + 1,
                ...user,
            })),
            type,
            period,
        });
    } catch (error: any) {
        console.error('Error fetching leaderboard:', error);
        return NextResponse.json(
            { error: 'Failed to fetch leaderboard' },
            { status: 500 }
        );
    }
}

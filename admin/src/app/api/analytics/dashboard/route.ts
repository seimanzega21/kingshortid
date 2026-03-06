import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { requireAdmin } from '@/lib/auth';

const prisma = new PrismaClient();

// GET /api/analytics/dashboard
export async function GET(req: NextRequest) {
    try {
        await requireAdmin(req);

        // Get real-time stats
        const now = new Date();
        const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const last7Days = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        const last30Days = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

        // Total counts
        const [totalUsers, totalDramas, totalEpisodes, activeUsers] = await Promise.all([
            prisma.user.count(),
            prisma.drama.count({ where: { isActive: true } }),
            prisma.episode.count({ where: { isActive: true } }),
            prisma.user.count({
                where: {
                    watchHistory: {
                        some: {
                            watchedAt: { gte: last7Days },
                        },
                    },
                },
            }),
        ]);

        // Revenue (coin purchases in last 30 days)
        const revenueData = await prisma.coinTransaction.aggregate({
            where: {
                type: 'topup',
                createdAt: { gte: last30Days },
            },
            _sum: { amount: true },
        });

        const totalRevenue = revenueData._sum.amount || 0;

        // Growth metrics
        const [newUsersToday, newUsersWeek, totalWatchHours] = await Promise.all([
            prisma.user.count({
                where: { createdAt: { gte: last24Hours } },
            }),
            prisma.user.count({
                where: { createdAt: { gte: last7Days } },
            }),
            prisma.watchHistory.aggregate({
                where: { watchedAt: { gte: last30Days } },
                _sum: { progress: true },
            }),
        ]);

        // Top dramas by views (last 7 days)
        const topDramas = await prisma.drama.findMany({
            where: { isActive: true },
            orderBy: { views: 'desc' },
            take: 5,
            select: {
                id: true,
                title: true,
                views: true,
                rating: true,
                genres: true,
            },
        });

        // User retention (simplified)
        const dayAgoUsers = await prisma.user.count({
            where: { createdAt: { lte: last24Hours, gte: last7Days } },
        });

        const activeOldUsers = await prisma.user.count({
            where: {
                createdAt: { lte: last24Hours, gte: last7Days },
                watchHistory: {
                    some: { watchedAt: { gte: last24Hours } },
                },
            },
        });

        const retentionRate = dayAgoUsers > 0
            ? Math.round((activeOldUsers / dayAgoUsers) * 100)
            : 0;

        // VIP subscribers
        const vipCount = await prisma.user.count({
            where: {
                vipStatus: true,
                OR: [
                    { vipExpiry: null },
                    { vipExpiry: { gte: now } },
                ],
            },
        });

        // Daily watch trends (last 7 days)
        const dailyWatches: Array<{ date: string; count: number }> = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            date.setHours(0, 0, 0, 0);

            const nextDate = new Date(date);
            nextDate.setDate(nextDate.getDate() + 1);

            const count = await prisma.watchHistory.count({
                where: {
                    watchedAt: {
                        gte: date,
                        lt: nextDate,
                    },
                },
            });

            dailyWatches.push({
                date: date.toISOString().split('T')[0],
                count,
            });
        }

        return NextResponse.json({
            overview: {
                totalUsers,
                totalDramas,
                totalEpisodes,
                activeUsers,
                vipCount,
                totalRevenue,
                retentionRate,
            },
            growth: {
                newUsersToday,
                newUsersWeek,
                totalWatchHours: Math.round((totalWatchHours._sum.progress || 0) / 60),
            },
            topDramas,
            dailyWatches,
            timestamp: now.toISOString(),
        });
    } catch (error) {
        console.error('Analytics dashboard error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

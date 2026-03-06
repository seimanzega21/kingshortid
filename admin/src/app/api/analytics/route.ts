import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/analytics - Get analytics data
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const period = searchParams.get('period') || '7d'; // 7d, 30d, 90d

        // Get date range
        const now = new Date();
        let startDate = new Date();
        if (period === '7d') startDate.setDate(now.getDate() - 7);
        else if (period === '30d') startDate.setDate(now.getDate() - 30);
        else startDate.setDate(now.getDate() - 90);

        // Get daily views (from watch history)
        const dailyViews = await prisma.watchHistory.groupBy({
            by: ['watchedAt'],
            _count: { id: true },
            where: {
                watchedAt: { gte: startDate }
            },
            orderBy: { watchedAt: 'asc' }
        });

        // Get top dramas by views
        const topDramas = await prisma.drama.findMany({
            take: 10,
            orderBy: { views: 'desc' },
            select: {
                id: true,
                title: true,
                views: true,
                rating: true,
                _count: {
                    select: { episodes: true }
                }
            }
        });

        // Get user growth
        const userGrowth = await prisma.user.groupBy({
            by: ['createdAt'],
            _count: { id: true },
            where: {
                createdAt: { gte: startDate }
            },
            orderBy: { createdAt: 'asc' }
        });

        // Get total stats
        const [totalViews, totalUsers, totalDramas, totalRevenue] = await Promise.all([
            prisma.drama.aggregate({ _sum: { views: true } }),
            prisma.user.count(),
            prisma.drama.count(),
            prisma.coinTransaction.aggregate({
                _sum: { amount: true },
                where: { type: 'topup' }
            })
        ]);

        // Format viewership data for chart
        const viewershipData = formatDailyData(dailyViews, startDate, now);

        // Format user growth for chart
        const userGrowthData = formatDailyData(userGrowth, startDate, now);

        return NextResponse.json({
            viewershipData,
            userGrowthData,
            topDramas: topDramas.map(d => ({
                ...d,
                episodes: d._count.episodes
            })),
            stats: {
                totalViews: totalViews._sum.views || 0,
                totalUsers,
                totalDramas,
                totalRevenue: totalRevenue._sum.amount || 0
            }
        });
    } catch (error) {
        console.error('Get analytics error:', error);
        return NextResponse.json(
            { message: 'Failed to get analytics' },
            { status: 500 }
        );
    }
}

function formatDailyData(data: any[], startDate: Date, endDate: Date) {
    const dayNames = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];
    const result = [];

    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        const found = data.find(item => {
            const itemDate = new Date(item.watchedAt || item.createdAt);
            return itemDate.toISOString().split('T')[0] === dateStr;
        });

        result.push({
            name: dayNames[d.getDay()],
            date: dateStr,
            value: found?._count?.id || 0
        });
    }

    return result.slice(-7); // Last 7 entries for weekly view
}

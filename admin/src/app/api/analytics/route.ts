import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/analytics - Get analytics data
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const period = searchParams.get('period') || '7d'; // 7d, 30d, 90d

        // Get date range
        const now = new Date();
        const startDate = new Date();
        let daysBack = 7;
        if (period === '30d') daysBack = 30;
        else if (period === '90d') daysBack = 90;
        startDate.setDate(now.getDate() - daysBack);
        startDate.setHours(0, 0, 0, 0);

        // Get daily views - group by date using raw SQL to avoid timestamp precision issue
        const dailyViewsRaw: Array<{ date: string; count: bigint }> = await prisma.$queryRaw`
            SELECT DATE(watched_at AT TIME ZONE 'Asia/Jakarta') as date, COUNT(*) as count
            FROM watch_history
            WHERE watched_at >= ${startDate}
            GROUP BY DATE(watched_at AT TIME ZONE 'Asia/Jakarta')
            ORDER BY date ASC
        `;

        // Get user growth grouped by day
        const userGrowthRaw: Array<{ date: string; count: bigint }> = await prisma.$queryRaw`
            SELECT DATE(created_at AT TIME ZONE 'Asia/Jakarta') as date, COUNT(*) as count
            FROM users
            WHERE created_at >= ${startDate}
            GROUP BY DATE(created_at AT TIME ZONE 'Asia/Jakarta')
            ORDER BY date ASC
        `;

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

        // Get total stats
        const [totalViews, totalUsers, totalDramas, totalRevenue] = await Promise.all([
            prisma.drama.aggregate({ _sum: { views: true } }),
            prisma.user.count(),
            prisma.drama.count(),
            // Revenue dari tabel payments (completed), bukan coin transactions
            prisma.payment.aggregate({
                _sum: { amount: true },
                where: { status: 'completed' }
            })
        ]);

        // Format viewership data for chart
        const viewershipData = formatDailyData(dailyViewsRaw, startDate, now, daysBack);

        // Format user growth for chart
        const userGrowthData = formatDailyData(userGrowthRaw, startDate, now, daysBack);

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

function formatDailyData(
    data: Array<{ date: string; count: bigint }>,
    startDate: Date,
    endDate: Date,
    daysBack: number
) {
    const dayNames = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];

    // Build a map of date -> count for O(1) lookup
    const countMap = new Map<string, number>();
    for (const row of data) {
        const dateStr = typeof row.date === 'string'
            ? row.date.split('T')[0]
            : new Date(row.date).toISOString().split('T')[0];
        countMap.set(dateStr, Number(row.count));
    }

    const result = [];
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        result.push({
            name: daysBack <= 7
                ? dayNames[d.getDay()]
                : `${d.getDate()}/${d.getMonth() + 1}`,
            date: dateStr,
            value: countMap.get(dateStr) || 0
        });
    }

    return result;
}

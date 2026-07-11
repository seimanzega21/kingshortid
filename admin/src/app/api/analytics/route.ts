import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/analytics - Get analytics data
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const period = searchParams.get('period') || '7d';

        const now = new Date();
        const startDate = new Date();
        let daysBack = 7;
        if (period === '30d') daysBack = 30;
        else if (period === '90d') daysBack = 90;
        startDate.setDate(now.getDate() - daysBack);
        startDate.setHours(0, 0, 0, 0);

        // Fetch all watch history records in range (timestamp level)
        const rawViews = await prisma.watchHistory.findMany({
            select: { watchedAt: true },
            where: { watchedAt: { gte: startDate } },
            orderBy: { watchedAt: 'asc' },
        });

        // Fetch user registrations in range
        const rawUsers = await prisma.user.findMany({
            select: { createdAt: true },
            where: { createdAt: { gte: startDate } },
            orderBy: { createdAt: 'asc' },
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
                _count: { select: { episodes: true } }
            }
        });

        // Get total stats
        const [totalViews, totalUsers, totalDramas, totalRevenue] = await Promise.all([
            prisma.drama.aggregate({ _sum: { views: true } }),
            prisma.user.count(),
            prisma.drama.count(),
            // Revenue dari coin topup (tabel payments belum digunakan)
            prisma.coinTransaction.aggregate({
                _sum: { amount: true },
                where: { type: 'topup' }
            })
        ]);

        // Aggregate per day (WIB = UTC+7)
        const viewershipData = aggregateByDay(
            rawViews.map(r => r.watchedAt),
            startDate,
            now,
            daysBack
        );
        const userGrowthData = aggregateByDay(
            rawUsers.map(r => r.createdAt),
            startDate,
            now,
            daysBack
        );

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

// Aggregate timestamps into daily counts, respecting WIB (UTC+7) timezone
function aggregateByDay(timestamps: Date[], startDate: Date, endDate: Date, daysBack: number) {
    const dayNames = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab'];
    const WIB_OFFSET_MS = 7 * 60 * 60 * 1000;

    // Build day->count map
    const countMap = new Map<string, number>();
    for (const ts of timestamps) {
        const wibDate = new Date(ts.getTime() + WIB_OFFSET_MS);
        const key = wibDate.toISOString().split('T')[0]; // YYYY-MM-DD
        countMap.set(key, (countMap.get(key) || 0) + 1);
    }

    const result = [];
    const cur = new Date(startDate);
    while (cur <= endDate) {
        const wibCur = new Date(cur.getTime() + WIB_OFFSET_MS);
        const key = wibCur.toISOString().split('T')[0];
        const label = daysBack <= 7
            ? dayNames[cur.getDay()]
            : `${cur.getDate()}/${cur.getMonth() + 1}`;
        result.push({ name: label, date: key, value: countMap.get(key) || 0 });
        cur.setDate(cur.getDate() + 1);
    }

    return result;
}

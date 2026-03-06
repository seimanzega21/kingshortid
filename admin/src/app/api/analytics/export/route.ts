import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/auth';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

/**
 * POST /api/analytics/export
 * Export analytics data as CSV or JSON
 */
export async function POST(request: NextRequest) {
    try {
        await requireAdmin(request);

        const body = await request.json();
        const { format = 'json', type = 'overview', dateRange } = body;

        const now = new Date();
        const startDate = dateRange?.start
            ? new Date(dateRange.start)
            : new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); // Last 30 days
        const endDate = dateRange?.end
            ? new Date(dateRange.end)
            : now;

        let data: any = {};

        switch (type) {
            case 'overview':
                data = await getOverviewData(startDate, endDate);
                break;
            case 'users':
                data = await getUsersData(startDate, endDate);
                break;
            case 'content':
                data = await getContentData(startDate, endDate);
                break;
            case 'revenue':
                data = await getRevenueData(startDate, endDate);
                break;
            default:
                return NextResponse.json({ error: 'Invalid export type' }, { status: 400 });
        }

        if (format === 'csv') {
            const csv = convertToCSV(data);
            return new NextResponse(csv, {
                headers: {
                    'Content-Type': 'text/csv',
                    'Content-Disposition': `attachment; filename="analytics-${type}-${Date.now()}.csv"`,
                },
            });
        }

        return NextResponse.json({
            data,
            metadata: {
                type,
                dateRange: { start: startDate, end: endDate },
                exportedAt: now.toISOString(),
            },
        });
    } catch (error: any) {
        console.error('Error exporting analytics:', error);
        return NextResponse.json(
            { error: 'Failed to export analytics' },
            { status: 500 }
        );
    }
}

async function getOverviewData(startDate: Date, endDate: Date) {
    const [totalUsers, totalDramas, totalEpisodes, totalViews] = await Promise.all([
        prisma.user.count(),
        prisma.drama.count({ where: { isActive: true } }),
        prisma.episode.count({ where: { isActive: true } }),
        prisma.watchHistory.count({
            where: { watchedAt: { gte: startDate, lte: endDate } },
        }),
    ]);

    return {
        totalUsers,
        totalDramas,
        totalEpisodes,
        totalViews,
        period: { start: startDate, end: endDate },
    };
}

async function getUsersData(startDate: Date, endDate: Date) {
    const users = await prisma.user.findMany({
        where: { createdAt: { gte: startDate, lte: endDate } },
        select: {
            id: true,
            email: true,
            name: true,
            coins: true,
            vipStatus: true,
            createdAt: true,
            _count: {
                select: {
                    watchHistory: true,
                },
            },
        },
        orderBy: { createdAt: 'desc' },
    });

    return users;
}

async function getContentData(startDate: Date, endDate: Date) {
    const dramas = await prisma.drama.findMany({
        where: {
            createdAt: { gte: startDate, lte: endDate },
        },
        select: {
            id: true,
            title: true,
            genres: true,
            views: true,
            rating: true,
            totalEpisodes: true,
            createdAt: true,
        },
        orderBy: { views: 'desc' },
    });

    return dramas;
}

async function getRevenueData(startDate: Date, endDate: Date) {
    const transactions = await prisma.coinTransaction.findMany({
        where: {
            type: 'topup',
            createdAt: { gte: startDate, lte: endDate },
        },
        select: {
            id: true,
            userId: true,
            amount: true,
            description: true,
            createdAt: true,
        },
        orderBy: { createdAt: 'desc' },
    });

    const totalRevenue = transactions.reduce((sum, t) => sum + t.amount, 0);

    return {
        transactions,
        totalRevenue,
    };
}

function convertToCSV(data: any): string {
    if (Array.isArray(data)) {
        if (data.length === 0) return '';

        const headers = Object.keys(data[0]);
        const rows = data.map(item =>
            headers.map(header => {
                const value = item[header];
                if (typeof value === 'object' && value !== null) {
                    return JSON.stringify(value);
                }
                return `"${value}"`;
            }).join(',')
        );

        return [headers.join(','), ...rows].join('\n');
    } else {
        const headers = Object.keys(data);
        const values = headers.map(h => data[h]);
        return [headers.join(','), values.join(',')].join('\n');
    }
}

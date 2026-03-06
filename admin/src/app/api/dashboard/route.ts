import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// In-memory cache — dashboard doesn't need real-time data
let cache: { data: any; ts: number } | null = null;
const CACHE_TTL = 30_000; // 30 seconds

// GET /api/dashboard — Stats from Supabase (Prisma)
export async function GET(request: NextRequest) {
    try {
        // Return cached data if fresh (instant response)
        if (cache && Date.now() - cache.ts < CACHE_TTL) {
            return NextResponse.json(cache.data);
        }

        const now12hAgo = new Date(Date.now() - 12 * 60 * 60 * 1000);

        // All queries in parallel
        const [
            totalUsers,
            onlineUsers,
            totalDramas,
            activeDramas,
            totalEpisodes,
            viewsAgg,
            recentUsers,
            popularDramas,
            noCoverCount,
            noDescCount,
            noEpisodesCount,
            deactivatedCount,
            genericGenreCount,
        ] = await Promise.all([
            prisma.user.count(),
            prisma.user.count({
                where: { updatedAt: { gte: now12hAgo }, isActive: true },
            }),
            prisma.drama.count(),
            prisma.drama.count({ where: { isActive: true } }),
            prisma.episode.count(),
            prisma.drama.aggregate({ _sum: { views: true } }),
            prisma.user.findMany({
                take: 5,
                orderBy: { createdAt: 'desc' },
                select: { id: true, name: true, email: true, role: true, createdAt: true },
            }),
            prisma.drama.findMany({
                take: 4,
                where: { isActive: true },
                orderBy: { views: 'desc' },
                select: { id: true, title: true, cover: true, views: true },
            }),
            prisma.drama.count({
                where: { isActive: true, cover: { in: ['', 'https://placehold.co/300x400'] } },
            }),
            prisma.drama.count({
                where: { isActive: true, description: { in: ['', 'No description available'] } },
            }),
            prisma.drama.count({ where: { isActive: true, totalEpisodes: 0 } }),
            prisma.drama.count({ where: { isActive: false } }),
            prisma.drama.count({
                where: {
                    isActive: true,
                    OR: [
                        { genres: { isEmpty: true } },
                        { genres: { equals: ['Drama'] } },
                    ],
                },
            }),
        ]);

        const totalViews = viewsAgg._sum.views || 0;
        const healthyCount = activeDramas - noCoverCount - noDescCount - noEpisodesCount - genericGenreCount;

        const result = {
            stats: {
                totalUsers,
                activeUsers: totalUsers,
                onlineUsers,
                totalDramas,
                activeDramas,
                inactiveDramas: deactivatedCount,
                totalEpisodes,
                totalViews,
            },
            dataHealth: {
                healthy: Math.max(0, healthyCount),
                genericGenre: genericGenreCount,
                noDescription: noDescCount,
                noCover: noCoverCount,
                noEpisodes: noEpisodesCount,
                deactivated: deactivatedCount,
            },
            recentUsers,
            popularDramas,
            recentDramas: [],
            source: 'supabase',
        };

        // Cache for 30 seconds
        cache = { data: result, ts: Date.now() };

        return NextResponse.json(result);
    } catch (error) {
        console.error('Dashboard error:', error);
        return NextResponse.json(
            { message: 'Failed to fetch dashboard stats' },
            { status: 500 }
        );
    }
}

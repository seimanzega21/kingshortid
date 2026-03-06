import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyAuth } from '@/lib/auth';

// POST /api/sync/queue - Submit offline actions queue
export async function POST(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const { actions } = await request.json();

        if (!Array.isArray(actions) || actions.length === 0) {
            return NextResponse.json(
                { error: 'Invalid actions array' },
                { status: 400 }
            );
        }

        const results = {
            processed: 0,
            failed: 0,
            errors: [] as string[],
        };

        for (const action of actions) {
            try {
                switch (action.type) {
                    case 'watch_progress':
                        await processWatchProgress(user.id, action.data);
                        break;
                    case 'like':
                        await processLike(user.id, action.data);
                        break;
                    case 'favorite':
                        await processFavorite(user.id, action.data);
                        break;
                    case 'watchlist':
                        await processWatchlist(user.id, action.data);
                        break;
                    case 'check_in':
                        await processCheckIn(user.id, action.data);
                        break;
                    default:
                        results.errors.push(`Unknown action type: ${action.type}`);
                        results.failed++;
                        continue;
                }
                results.processed++;
            } catch (error: any) {
                results.failed++;
                results.errors.push(`${action.type}: ${error.message}`);
            }
        }

        return NextResponse.json({
            success: true,
            ...results,
        });
    } catch (error: any) {
        console.error('Sync error:', error);
        return NextResponse.json(
            { error: 'Failed to sync', message: error.message },
            { status: 500 }
        );
    }
}

// GET /api/sync/queue - Get pending sync status
export async function GET(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        // Return user's sync status
        const syncStatus = {
            lastSyncAt: new Date().toISOString(),
            serverTime: new Date().toISOString(),
            userId: user.id,
        };

        return NextResponse.json(syncStatus);
    } catch (error: any) {
        return NextResponse.json(
            { error: 'Failed to get sync status' },
            { status: 500 }
        );
    }
}

// Helper: Process watch progress
async function processWatchProgress(
    userId: string,
    data: { dramaId: string; episodeId: string; progress: number; episodeNumber: number }
) {
    await prisma.watchHistory.upsert({
        where: {
            userId_dramaId_episodeId: {
                userId,
                dramaId: data.dramaId,
                episodeId: data.episodeId,
            },
        },
        update: {
            progress: data.progress,
            watchedAt: new Date(),
        },
        create: {
            userId,
            dramaId: data.dramaId,
            episodeId: data.episodeId,
            episodeNumber: data.episodeNumber,
            progress: data.progress,
        },
    });

    // Update user's total watch time
    await prisma.user.update({
        where: { id: userId },
        data: {
            totalWatchTime: { increment: Math.floor(data.progress / 100 * 60) }, // Rough estimate
        },
    });
}

// Helper: Process like
async function processLike(
    userId: string,
    data: { dramaId: string; action: 'add' | 'remove' }
) {
    if (data.action === 'add') {
        await prisma.drama.update({
            where: { id: data.dramaId },
            data: { likes: { increment: 1 } },
        });
    } else {
        await prisma.drama.update({
            where: { id: data.dramaId },
            data: { likes: { decrement: 1 } },
        });
    }
}

// Helper: Process favorite
async function processFavorite(
    userId: string,
    data: { dramaId: string; action: 'add' | 'remove' }
) {
    if (data.action === 'add') {
        await prisma.favorite.upsert({
            where: {
                userId_dramaId: {
                    userId,
                    dramaId: data.dramaId,
                },
            },
            update: {},
            create: {
                userId,
                dramaId: data.dramaId,
            },
        });
    } else {
        await prisma.favorite.deleteMany({
            where: {
                userId,
                dramaId: data.dramaId,
            },
        });
    }
}

// Helper: Process watchlist
async function processWatchlist(
    userId: string,
    data: { dramaId: string; action: 'add' | 'remove' }
) {
    if (data.action === 'add') {
        await prisma.watchlist.upsert({
            where: {
                userId_dramaId: {
                    userId,
                    dramaId: data.dramaId,
                },
            },
            update: {},
            create: {
                userId,
                dramaId: data.dramaId,
            },
        });
    } else {
        await prisma.watchlist.deleteMany({
            where: {
                userId,
                dramaId: data.dramaId,
            },
        });
    }
}

// Helper: Process check-in
async function processCheckIn(
    userId: string,
    data: { date: string; reward: number }
) {
    const user = await prisma.user.findUnique({
        where: { id: userId },
        select: { lastCheckIn: true, checkInStreak: true },
    });

    if (!user) return;

    const checkInDate = new Date(data.date);
    const now = new Date();
    const lastCheckIn = user.lastCheckIn ? new Date(user.lastCheckIn) : null;

    // Check if already checked in today
    if (lastCheckIn && isSameDay(lastCheckIn, checkInDate)) {
        return; // Already checked in
    }

    // Calculate streak
    let newStreak = 1;
    if (lastCheckIn && isYesterday(lastCheckIn, checkInDate)) {
        newStreak = user.checkInStreak + 1;
    }

    // Update user
    await prisma.user.update({
        where: { id: userId },
        data: {
            lastCheckIn: checkInDate,
            checkInStreak: newStreak,
            coins: { increment: data.reward },
        },
    });

    // Create transaction
    await prisma.coinTransaction.create({
        data: {
            userId,
            type: 'earn',
            amount: data.reward,
            description: `Daily check-in (Day ${newStreak})`,
        },
    });
}

function isSameDay(date1: Date, date2: Date): boolean {
    return (
        date1.getFullYear() === date2.getFullYear() &&
        date1.getMonth() === date2.getMonth() &&
        date1.getDate() === date2.getDate()
    );
}

function isYesterday(lastDate: Date, currentDate: Date): boolean {
    const yesterday = new Date(currentDate);
    yesterday.setDate(yesterday.getDate() - 1);
    return isSameDay(lastDate, yesterday);
}

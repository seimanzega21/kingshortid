import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

/**
 * GET /api/notifications/preferences
 * Get user's email notification preferences
 */
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const userData = await prisma.user.findUnique({
            where: { id: user.id },
            select: {
                notifyEpisodes: true,
                notifyCoins: true,
                notifySystem: true,
            },
        });

        return NextResponse.json({
            preferences: {
                newEpisodes: userData?.notifyEpisodes ?? true,
                coinRewards: userData?.notifyCoins ?? true,
                systemUpdates: userData?.notifySystem ?? true,
            },
        });
    } catch (error: any) {
        console.error('Error fetching preferences:', error);
        return NextResponse.json(
            { error: 'Failed to fetch preferences' },
            { status: 500 }
        );
    }
}

/**
 * PUT /api/notifications/preferences
 * Update user's email notification preferences
 */
export async function PUT(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { newEpisodes, coinRewards, systemUpdates } = body;

        await prisma.user.update({
            where: { id: user.id },
            data: {
                notifyEpisodes: newEpisodes ?? undefined,
                notifyCoins: coinRewards ?? undefined,
                notifySystem: systemUpdates ?? undefined,
            },
        });

        return NextResponse.json({
            message: 'Preferences updated successfully',
            preferences: {
                newEpisodes,
                coinRewards,
                systemUpdates,
            },
        });
    } catch (error: any) {
        console.error('Error updating preferences:', error);
        return NextResponse.json(
            { error: 'Failed to update preferences' },
            { status: 500 }
        );
    }
}

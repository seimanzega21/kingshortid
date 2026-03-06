import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/user/notifications/settings - Get notification preferences
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        }

        const dbUser = await prisma.user.findUnique({
            where: { id: user.id },
            select: {
                notifyEpisodes: true,
                notifyCoins: true,
                notifySystem: true
            }
        });

        if (!dbUser) {
            return NextResponse.json({ message: 'User not found' }, { status: 404 });
        }

        return NextResponse.json({
            newEpisodes: dbUser.notifyEpisodes,
            coinRewards: dbUser.notifyCoins,
            systemUpdates: dbUser.notifySystem
        });

    } catch (error) {
        console.error('Get notification settings error:', error);
        return NextResponse.json({ message: 'Error fetching settings' }, { status: 500 });
    }
}

// PUT /api/user/notifications/settings - Update notification preferences
export async function PUT(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        }

        const { newEpisodes, coinRewards, systemUpdates } = await request.json();

        // Build update object only with provided fields
        const updateData: any = {};
        if (newEpisodes !== undefined) updateData.notifyEpisodes = newEpisodes;
        if (coinRewards !== undefined) updateData.notifyCoins = coinRewards;
        if (systemUpdates !== undefined) updateData.notifySystem = systemUpdates;

        await prisma.user.update({
            where: { id: user.id },
            data: updateData
        });

        return NextResponse.json({
            success: true,
            message: 'Notification settings updated'
        });

    } catch (error) {
        console.error('Update notification settings error:', error);
        return NextResponse.json({ message: 'Error updating settings' }, { status: 500 });
    }
}

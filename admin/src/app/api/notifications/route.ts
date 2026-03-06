import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/notifications/push-token - Save user's push token
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { token } = await request.json();

        if (!token) {
            return NextResponse.json(
                { error: 'Token is required' },
                { status: 400 }
            );
        }

        await prisma.user.update({
            where: { id: user.id },
            data: { pushToken: token },
        });

        return NextResponse.json({ message: 'Push token saved' });
    } catch (error: any) {
        console.error('Error saving push token:', error);
        return NextResponse.json(
            { error: 'Failed to save push token' },
            { status: 500 }
        );
    }
}

// GET /api/notifications/preferences - Get notification preferences
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const preferences = await prisma.user.findUnique({
            where: { id: user.id },
            select: {
                notifyEpisodes: true,
                notifyCoins: true,
                notifySystem: true,
            },
        });

        return NextResponse.json(
            preferences || {
                notifyEpisodes: true,
                notifyCoins: true,
                notifySystem: true,
            }
        );
    } catch (error: any) {
        console.error('Error fetching notification preferences:', error);
        return NextResponse.json(
            { error: 'Failed to fetch preferences' },
            { status: 500 }
        );
    }
}

// PUT /api/notifications/preferences - Update notification preferences
export async function PUT(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { notifyEpisodes, notifyCoins, notifySystem } = await request.json();

        await prisma.user.update({
            where: { id: user.id },
            data: {
                ...(notifyEpisodes !== undefined && { notifyEpisodes }),
                ...(notifyCoins !== undefined && { notifyCoins }),
                ...(notifySystem !== undefined && { notifySystem }),
            },
        });

        return NextResponse.json({ message: 'Preferences updated' });
    } catch (error: any) {
        console.error('Error updating notification preferences:', error);
        return NextResponse.json(
            { error: 'Failed to update preferences' },
            { status: 500 }
        );
    }
}

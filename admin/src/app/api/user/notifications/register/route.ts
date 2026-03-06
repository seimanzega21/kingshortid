import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/user/notifications/register - Register/update push token
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        }

        const { token, platform } = await request.json();

        if (!token) {
            return NextResponse.json({ message: 'Token is required' }, { status: 400 });
        }

        // Update user's push token
        await prisma.user.update({
            where: { id: user.id },
            data: { pushToken: token }
        });

        return NextResponse.json({
            success: true,
            message: 'Push token registered successfully'
        });

    } catch (error) {
        console.error('Push token registration error:', error);
        return NextResponse.json({ message: 'Error registering push token' }, { status: 500 });
    }
}

// DELETE /api/user/notifications/register - Unregister push token
export async function DELETE(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        }

        // Remove user's push token
        await prisma.user.update({
            where: { id: user.id },
            data: { pushToken: null }
        });

        return NextResponse.json({
            success: true,
            message: 'Push token unregistered successfully'
        });

    } catch (error) {
        console.error('Push token unregistration error:', error);
        return NextResponse.json({ message: 'Error unregistering push token' }, { status: 500 });
    }
}

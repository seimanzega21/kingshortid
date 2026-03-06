import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

/**
 * GET /api/subscriptions/status
 * Get current user's subscription status
 */
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const subscription = await prisma.subscription.findUnique({
            where: { userId: user.id },
        });

        if (!subscription) {
            return NextResponse.json({
                subscribed: false,
                tier: 'basic',
                status: 'none',
            });
        }

        // Check if expired
        const now = new Date();
        if (subscription.endDate < now && subscription.status === 'active') {
            await prisma.subscription.update({
                where: { id: subscription.id },
                data: { status: 'expired' },
            });
            subscription.status = 'expired';
        }

        return NextResponse.json({
            subscribed: subscription.status === 'active',
            ...subscription,
        });
    } catch (error: any) {
        console.error('Error fetching subscription status:', error);
        return NextResponse.json(
            { error: 'Failed to fetch subscription status' },
            { status: 500 }
        );
    }
}

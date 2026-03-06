import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/subscriptions/create - Create or update subscription
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { tier, months } = body;

        if (!tier || !['basic', 'premium', 'vip'].includes(tier)) {
            return NextResponse.json(
                { error: 'Invalid tier' },
                { status: 400 }
            );
        }

        const duration = months || 1;
        const endDate = new Date();
        endDate.setMonth(endDate.getMonth() + duration);

        // Check for existing subscription
        const existingSub = await prisma.subscription.findUnique({
            where: { userId: user.id },
        });

        let subscription;
        if (existingSub) {
            // Update existing subscription
            subscription = await prisma.subscription.update({
                where: { id: existingSub.id },
                data: {
                    tier,
                    status: 'active',
                    endDate,
                },
            });
        } else {
            // Create new subscription
            subscription = await prisma.subscription.create({
                data: {
                    userId: user.id,
                    tier,
                    status: 'trial', // Start with trial
                    endDate,
                },
            });
        }

        // Update user VIP status
        await prisma.user.update({
            where: { id: user.id },
            data: {
                vipStatus: tier === 'vip',
                vipExpiry: tier === 'vip' ? endDate : null,
            },
        });

        return NextResponse.json(subscription);
    } catch (error: any) {
        console.error('Error creating subscription:', error);
        return NextResponse.json(
            { error: 'Failed to create subscription' },
            { status: 500 }
        );
    }
}

// GET /api/subscriptions/status - Get user's subscription status
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
                tier: 'free',
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
        console.error('Error fetching subscription:', error);
        return NextResponse.json(
            { error: 'Failed to fetch subscription' },
            { status: 500 }
        );
    }
}

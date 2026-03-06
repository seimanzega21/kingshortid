import { NextRequest, NextResponse } from 'next/server';

// Define subscription tier benefits
export const SUBSCRIPTION_TIERS = [
    {
        id: 'basic',
        name: 'Basic',
        tier: 'basic',
        price: 0,
        currency: 'USD',
        duration: 30, // days
        features: [
            'Access to free content',
            'HD streaming (720p)',
            'Watch on 1 device',
            'Standard support',
        ],
    },
    {
        id: 'premium',
        name: 'Premium',
        tier: 'premium',
        price: 9.99,
        currency: 'USD',
        duration: 30,
        isPopular: true,
        features: [
            'All Basic features',
            'Ad-free experience',
            'Full HD streaming (1080p)',
            'Early access to new episodes',
            'Watch on 3 devices simultaneously',
            'Download up to 20 episodes',
            '100 bonus coins/month',
            'Priority support',
        ],
    },
    {
        id: 'vip',
        name: 'VIP',
        tier: 'vip',
        price: 19.99,
        currency: 'USD',
        duration: 30,
        features: [
            'All Premium features',
            'Access to VIP exclusive content',
            '4K Ultra HD streaming',
            'Watch on 5 devices simultaneously',
            'Unlimited downloads',
            'Exclusive VIP badges',
            '300 bonus coins/month',
            '24/7 Premium support',
            'Early access to beta features',
        ],
    },
];

/**
 * GET /api/subscriptions/tiers
 * Get all available subscription tiers with pricing and features
 */
export async function GET(request: NextRequest) {
    try {
        return NextResponse.json(SUBSCRIPTION_TIERS);
    } catch (error: any) {
        console.error('Error fetching subscription tiers:', error);
        return NextResponse.json(
            { error: 'Failed to fetch subscription tiers' },
            { status: 500 }
        );
    }
}

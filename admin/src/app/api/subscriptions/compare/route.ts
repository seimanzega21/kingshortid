import { NextRequest, NextResponse } from 'next/server';
import { SUBSCRIPTION_TIERS } from '../tiers/route';

/**
 * GET /api/subscriptions/compare
 * Get tier comparison data for UI display
 */
export async function GET(request: NextRequest) {
    try {
        // Feature categories for comparison
        const comparisonData = {
            categories: [
                {
                    name: 'Streaming Quality',
                    features: [
                        {
                            name: 'Video Quality',
                            basic: 'HD (720p)',
                            premium: 'Full HD (1080p)',
                            vip: '4K Ultra HD',
                        },
                        {
                            name: 'Ads',
                            basic: 'With Ads',
                            premium: 'Ad-free',
                            vip: 'Ad-free',
                        },
                    ],
                },
                {
                    name: 'Content Access',
                    features: [
                        {
                            name: 'Free Content',
                            basic: true,
                            premium: true,
                            vip: true,
                        },
                        {
                            name: 'Premium Content',
                            basic: false,
                            premium: true,
                            vip: true,
                        },
                        {
                            name: 'VIP Exclusive',
                            basic: false,
                            premium: false,
                            vip: true,
                        },
                        {
                            name: 'Early Access',
                            basic: false,
                            premium: true,
                            vip: true,
                        },
                    ],
                },
                {
                    name: 'Devices & Downloads',
                    features: [
                        {
                            name: 'Simultaneous Devices',
                            basic: '1',
                            premium: '3',
                            vip: '5',
                        },
                        {
                            name: 'Download Episodes',
                            basic: 'Not available',
                            premium: 'Up to 20',
                            vip: 'Unlimited',
                        },
                    ],
                },
                {
                    name: 'Rewards & Bonuses',
                    features: [
                        {
                            name: 'Bonus Coins/Month',
                            basic: '0',
                            premium: '100',
                            vip: '300',
                        },
                        {
                            name: 'Exclusive Badges',
                            basic: false,
                            premium: false,
                            vip: true,
                        },
                    ],
                },
                {
                    name: 'Support',
                    features: [
                        {
                            name: 'Customer Support',
                            basic: 'Standard',
                            premium: 'Priority',
                            vip: '24/7 Premium',
                        },
                        {
                            name: 'Beta Features',
                            basic: false,
                            premium: false,
                            vip: true,
                        },
                    ],
                },
            ],
            tiers: SUBSCRIPTION_TIERS,
        };

        return NextResponse.json(comparisonData);
    } catch (error: any) {
        console.error('Error fetching subscription comparison:', error);
        return NextResponse.json(
            { error: 'Failed to fetch subscription comparison' },
            { status: 500 }
        );
    }
}

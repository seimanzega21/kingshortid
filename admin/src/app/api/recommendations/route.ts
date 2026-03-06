import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import {
    getPersonalizedRecommendations,
    getTrendingDramas,
    getSimilarDramas,
    getMoodBasedRecommendations,
    updateUserPreferences,
} from '@/lib/recommendations';

// GET /api/recommendations/personalized
export async function GET(req: NextRequest) {
    try {
        const token = req.headers.get('authorization')?.replace('Bearer ', '');
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const payload = await getAuthUser(req);
        if (!payload || !payload.id) {
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }

        const { searchParams } = new URL(req.url);
        const type = searchParams.get('type') || 'personalized';
        const limit = parseInt(searchParams.get('limit') || '10');
        const dramaId = searchParams.get('dramaId');
        const mood = searchParams.get('mood') as any;

        let dramas;

        switch (type) {
            case 'trending':
                dramas = await getTrendingDramas(limit);
                break;
            case 'similar':
                if (!dramaId) {
                    return NextResponse.json({ error: 'dramaId required for similar' }, { status: 400 });
                }
                dramas = await getSimilarDramas(dramaId, limit);
                break;
            case 'mood':
                if (!mood) {
                    return NextResponse.json({ error: 'mood parameter required' }, { status: 400 });
                }
                dramas = await getMoodBasedRecommendations(mood, limit);
                break;
            case 'personalized':
            default:
                dramas = await getPersonalizedRecommendations(payload.id, limit);

                // Update user preferences async
                updateUserPreferences(payload.id).catch((err) =>
                    console.error('Failed to update preferences:', err)
                );
                break;
        }

        return NextResponse.json(dramas);
    } catch (error) {
        console.error('Recommendations error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

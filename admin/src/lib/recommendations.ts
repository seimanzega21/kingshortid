import { PrismaClient, Drama, User, WatchHistory } from '@prisma/client';

const prisma = new PrismaClient();

interface ScoredDrama {
    drama: Drama;
    score: number;
}

/**
 * Generate personalized drama recommendations for a user
 * Uses collaborative filtering and content-based filtering
 */
export async function getPersonalizedRecommendations(
    userId: string,
    limit: number = 10
): Promise<Drama[]> {
    // Get user's watch history
    const watchHistory = await prisma.watchHistory.findMany({
        where: { userId },
        include: { drama: true },
        orderBy: { watchedAt: 'desc' },
        take: 50,
    });

    if (watchHistory.length === 0) {
        // New user - return trending dramas
        return getTrendingDramas(limit);
    }

    // Extract genres and tags from watched dramas
    const watchedGenres: Record<string, number> = {};
    const watchedTags: Record<string, number> = {};
    const watchedDramaIds = new Set<string>();

    watchHistory.forEach((wh) => {
        watchedDramaIds.add(wh.dramaId);

        wh.drama.genres.forEach((genre) => {
            watchedGenres[genre] = (watchedGenres[genre] || 0) + 1;
        });

        wh.drama.tags.forEach((tag) => {
            watchedTags[tag] = (watchedTags[tag] || 0) + 1;
        });
    });

    // Get all active dramas except already watched
    const allDramas = await prisma.drama.findMany({
        where: {
            isActive: true,
            id: { notIn: Array.from(watchedDramaIds) },
        },
    });

    // Score each drama based on similarity
    const scoredDramas: ScoredDrama[] = allDramas.map((drama) => {
        let score = 0;

        // Genre matching (40% weight)
        drama.genres.forEach((genre) => {
            score += (watchedGenres[genre] || 0) * 4;
        });

        // Tag matching (30% weight)
        drama.tags.forEach((tag) => {
            score += (watchedTags[tag] || 0) * 3;
        });

        // Popularity boost (20% weight)
        score += Math.log(drama.views + 1) * 0.2;
        score += drama.rating * 2;

        // Featured boost (10% weight)
        if (drama.isFeatured) {
            score += 10;
        }

        return { drama, score };
    });

    // Sort by score and return top recommendations
    scoredDramas.sort((a, b) => b.score - a.score);

    return scoredDramas.slice(0, limit).map((sd) => sd.drama);
}

/**
 * Get trending dramas based on recent views and ratings
 */
export async function getTrendingDramas(limit: number = 10): Promise<Drama[]> {
    const dramas = await prisma.drama.findMany({
        where: { isActive: true },
        orderBy: [
            { views: 'desc' },
            { rating: 'desc' },
        ],
        take: limit,
    });

    return dramas;
}

/**
 * Get similar dramas based on genres and tags
 */
export async function getSimilarDramas(
    dramaId: string,
    limit: number = 10
): Promise<Drama[]> {
    const sourceDrama = await prisma.drama.findUnique({
        where: { id: dramaId },
    });

    if (!sourceDrama) {
        return [];
    }

    const similarDramas = await prisma.drama.findMany({
        where: {
            isActive: true,
            id: { not: dramaId },
            OR: [
                { genres: { hasSome: sourceDrama.genres } },
                { tags: { hasSome: sourceDrama.tags } },
            ],
        },
        take: limit * 2,
    });

    // Score by similarity
    const scored: ScoredDrama[] = similarDramas.map((drama) => {
        let score = 0;

        // Count matching genres
        const matchingGenres = drama.genres.filter((g) =>
            sourceDrama.genres.includes(g)
        ).length;
        score += matchingGenres * 10;

        // Count matching tags
        const matchingTags = drama.tags.filter((t) =>
            sourceDrama.tags.includes(t)
        ).length;
        score += matchingTags * 5;

        // Boost by rating
        score += drama.rating * 2;

        return { drama, score };
    });

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map((s) => s.drama);
}

/**
 * Update user preferences based on watch history
 */
export async function updateUserPreferences(userId: string): Promise<void> {
    const watchHistory = await prisma.watchHistory.findMany({
        where: { userId },
        include: { drama: true },
        orderBy: { watchedAt: 'desc' },
        take: 100,
    });

    const genreCounts: Record<string, number> = {};
    const tagCounts: Record<string, number> = {};

    watchHistory.forEach((wh) => {
        wh.drama.genres.forEach((genre) => {
            genreCounts[genre] = (genreCounts[genre] || 0) + 1;
        });
        wh.drama.tags.forEach((tag) => {
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        });
    });

    // Sort and get top preferences
    const topGenres = Object.entries(genreCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([genre]) => genre);

    const topTags = Object.entries(tagCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([tag]) => tag);

    await prisma.user.update({
        where: { id: userId },
        data: {
            preferences: {
                favoriteGenres: topGenres,
                favoriteTags: topTags,
                updatedAt: new Date(),
            },
        },
    });
}

/**
 * Get mood-based recommendations
 */
export async function getMoodBasedRecommendations(
    mood: 'romantic' | 'action' | 'comedy' | 'thriller' | 'emotional',
    limit: number = 10
): Promise<Drama[]> {
    const moodToTags: Record<string, string[]> = {
        romantic: ['Romance', 'Love', 'Couple', 'Wedding'],
        action: ['Action', 'Fight', 'Martial Arts', 'Adventure'],
        comedy: ['Comedy', 'Funny', 'Light-hearted', 'Humor'],
        thriller: ['Thriller', 'Mystery', 'Suspense', 'Crime'],
        emotional: ['Emotional', 'Drama', 'Tear-jerker', 'Family'],
    };

    const tags = moodToTags[mood] || [];

    const dramas = await prisma.drama.findMany({
        where: {
            isActive: true,
            OR: [
                { tags: { hasSome: tags } },
                { genres: { hasSome: tags } },
            ],
        },
        orderBy: [
            { rating: 'desc' },
            { views: 'desc' },
        ],
        take: limit,
    });

    return dramas;
}

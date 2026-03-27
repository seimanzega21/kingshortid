import { Hono } from 'hono';
import { asc, eq } from 'drizzle-orm';
import { getDb, parseJsonArray } from '../db';
import { categories, dramas } from '../db/schema';
import type { Env } from '../middleware/auth';

const categoriesRoute = new Hono<Env>();

// GET /api/categories
categoriesRoute.get('/', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const result = await db.select().from(categories).orderBy(asc(categories.order));
        return c.json(result);
    } catch (error) {
        console.error('Get categories error:', error);
        return c.json({ error: 'Failed to get categories' }, 500);
    }
});

// GET /api/genres — distinct genres from all active dramas
// Admin controls genres by editing drama genre fields
categoriesRoute.get('/genres', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const result = await db.select({ genres: dramas.genres })
            .from(dramas)
            .where(eq(dramas.isActive, true));

        // Extract all unique genres from JSON arrays
        const genreSet = new Set<string>();
        for (const row of result) {
            const parsed = parseJsonArray(row.genres);
            for (const g of parsed) {
                if (g && typeof g === 'string' && g.trim()) {
                    genreSet.add(g.trim());
                }
            }
        }

        const GENRE_EMOJI: Record<string, string> = {
            'Romance': '💕', 'Romantis': '💕', 'Action': '🎬', 'Aksi': '🎬',
            'Comedy': '😂', 'Komedi': '😂', 'Drama': '🎭', 'Fantasy': '✨',
            'Fantasi': '✨', 'Thriller': '😱', 'Historical': '🏛️', 'School': '🎓',
            'CEO': '💼', 'Mafia': '🔫', 'Wanita Kuat': '👸', 'Bisnis': '💼',
            'Keluarga': '👨‍👩‍👧', 'Wanita': '👩', 'Pria': '👨', 'Sistem': '⚡',
            'Urban': '🌆', 'Misteri': '🔍', 'Sakti': '⚔️', 'Dewa Perang': '⚔️',
        };

        const genres = Array.from(genreSet)
            .sort()
            .map(name => ({
                name,
                emoji: GENRE_EMOJI[name] || '🎬',
                label: `${GENRE_EMOJI[name] || '🎬'} ${name}`,
            }));

        return c.json(genres);
    } catch (error) {
        console.error('Get genres error:', error);
        return c.json({ error: 'Failed to get genres' }, 500);
    }
});

export default categoriesRoute;

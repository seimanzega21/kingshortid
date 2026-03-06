import { Hono } from 'hono';
import { asc } from 'drizzle-orm';
import { getDb } from '../db';
import { categories } from '../db/schema';
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

export default categoriesRoute;

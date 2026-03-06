import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { secureHeaders } from 'hono/secure-headers';

import type { Env } from './middleware/auth';
import { apiLimiter } from './middleware/rate-limit';

import auth from './routes/auth';
import dramasRoute from './routes/dramas';
import episodesRoute from './routes/episodes';
import userRoute from './routes/user';
import rewardsRoute from './routes/rewards';
import notificationsRoute from './routes/notifications';
import categoriesRoute from './routes/categories';
import settingsRoute from './routes/settings';
import adminRoute from './routes/admin';

const app = new Hono<Env>();

// Global middleware
app.use('*', cors({
    origin: '*',
    allowHeaders: ['Content-Type', 'Authorization'],
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
}));
app.use('*', secureHeaders());
app.use('*', logger());
app.use('/api/*', apiLimiter);

// Health check
app.get('/', (c) => c.json({
    status: 'ok',
    service: 'KingShortID API',
    version: '2.0.0',
    runtime: 'Cloudflare Workers',
}));

app.get('/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }));

// Mount routes
app.route('/api/auth', auth);
app.route('/api/dramas', dramasRoute);
app.route('/api/episodes', episodesRoute);
app.route('/api/user', userRoute);
app.route('/api/rewards', rewardsRoute);
app.route('/api/notifications', notificationsRoute);
app.route('/api/categories', categoriesRoute);
app.route('/api/settings', settingsRoute);
app.route('/api/admin', adminRoute);

// 404 handler
app.notFound((c) => c.json({ error: 'Not found', path: c.req.path }, 404));

// Error handler
app.onError((err, c) => {
    console.error('Unhandled error:', err);
    return c.json({ error: 'Internal server error' }, 500);
});

export default app;

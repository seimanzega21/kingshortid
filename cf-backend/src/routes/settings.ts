import { Hono } from 'hono';
import { getDb } from '../db';
import { sql } from 'drizzle-orm';
import type { Env } from '../middleware/auth';

const settingsRoute = new Hono<Env>();

// GET /api/settings - Get all settings as a flat object
settingsRoute.get('/', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const rows = await db.execute(sql`SELECT key, value FROM app_settings`);

        const settings: Record<string, string> = {};
        for (const row of rows as any[]) {
            settings[row.key] = row.value;
        }

        return c.json({
            appName: settings.appName || 'KingShort',
            appDescription: settings.appDescription || '',
            maintenanceMode: settings.maintenanceMode === 'true',
            registrationsOpen: settings.registrationsOpen !== 'false',
            language: settings.language || 'id',
            currency: settings.currency || 'IDR',
            termsUrl: settings.termsUrl || '',
            privacyUrl: settings.privacyUrl || '',
            contactEmail: settings.contactEmail || '',
            contactPhone: settings.contactPhone || '',
            maxLoginAttempts: parseInt(settings.maxLoginAttempts || '5'),
            sessionTimeout: parseInt(settings.sessionTimeout || '24'),
            twoFactorEnabled: settings.twoFactorEnabled === 'true',

            // Ad settings
            adsEnabled: settings.adsEnabled !== 'false',
            adsBannerEnabled: settings.adsBannerEnabled !== 'false',
            adsInterstitialEnabled: settings.adsInterstitialEnabled !== 'false',
            adsRewardedEnabled: settings.adsRewardedEnabled !== 'false',
            adsFrequency: parseInt(settings.adsFrequency || '5'),
            maxDailyAds: parseInt(settings.maxDailyAds || '10'),
            interstitialCloseDelay: parseInt(settings.interstitialCloseDelay || '5'),
            rewardedCoinsAmount: parseInt(settings.rewardedCoinsAmount || '10'),
            bannerPosition: settings.bannerPosition || 'bottom',
            adUnitBanner: settings.adUnitBanner || '',
            adUnitInterstitial: settings.adUnitInterstitial || '',
            adUnitRewarded: settings.adUnitRewarded || '',
        });
    } catch (error) {
        console.error('Get settings error:', error);
        return c.json({ error: 'Failed to get settings' }, 500);
    }
});

// POST /api/settings - Save all settings
settingsRoute.post('/', async (c) => {
    try {
        const body = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const now = Math.floor(Date.now() / 1000);

        const keys = [
            'appName', 'appDescription', 'maintenanceMode', 'registrationsOpen',
            'language', 'currency', 'termsUrl', 'privacyUrl',
            'contactEmail', 'contactPhone',
            'maxLoginAttempts', 'sessionTimeout', 'twoFactorEnabled',
            // Ad settings
            'adsEnabled', 'adsBannerEnabled', 'adsInterstitialEnabled',
            'adsRewardedEnabled', 'adsFrequency', 'maxDailyAds',
            'interstitialCloseDelay', 'rewardedCoinsAmount', 'bannerPosition',
            'adUnitBanner', 'adUnitInterstitial', 'adUnitRewarded',
        ];

        // Upsert each setting using Drizzle raw SQL
        for (const k of keys) {
            if (body[k] !== undefined) {
                await db.execute(sql`
                    INSERT INTO app_settings (key, value, updated_at)
                    VALUES (${k}, ${String(body[k])}, ${now})
                    ON CONFLICT (key) DO UPDATE SET value = ${String(body[k])}, updated_at = ${now}
                `);
            }
        }

        return c.json({ success: true, message: 'Settings saved' });
    } catch (error) {
        console.error('Save settings error:', error);
        return c.json({ error: 'Failed to save settings' }, 500);
    }
});

export default settingsRoute;

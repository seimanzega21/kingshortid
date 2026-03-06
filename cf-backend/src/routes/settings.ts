import { Hono } from 'hono';
import { getDb } from '../db';
import { sql } from 'drizzle-orm';
import type { Env } from '../middleware/auth';

const settingsRoute = new Hono<Env>();

// Simple key-value settings table (app_settings)
// Stores all app settings as JSON key-value pairs

// GET /api/settings - Get all settings as a flat object
settingsRoute.get('/', async (c) => {
    try {
        const db = c.env.DB;
        const result = await db.prepare('SELECT key, value FROM app_settings');

        const settings: Record<string, string> = {};
        for (const row of result.results as any[]) {
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
        const db = c.env.DB;
        const now = Math.floor(Date.now() / 1000);

        // Upsert each setting
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

        const stmt = db.prepare(
            'INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at'
        );

        const batch = keys
            .filter(k => body[k] !== undefined)
            .map(k => stmt.bind(k, String(body[k]), now));

        if (batch.length > 0) {
            await db.batch(batch);
        }

        return c.json({ success: true, message: 'Settings saved' });
    } catch (error) {
        console.error('Save settings error:', error);
        return c.json({ error: 'Failed to save settings' }, 500);
    }
});

export default settingsRoute;

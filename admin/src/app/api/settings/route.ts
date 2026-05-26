import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

const DEFAULT_SETTINGS = {
    // Basic
    appName: "KingShort",
    appDescription: "Platform Drama Pendek Terbaik",
    maintenanceMode: false,
    registrationsOpen: true,

    // Localization
    currency: "IDR",
    language: "id",

    // === BANNERS ===
    bannerMode: 'auto',
    bannerRotationDays: 2,

    // === IKLAN (ADS) ===
    adsEnabled: true,
    adsBannerEnabled: true,
    adsInterstitialEnabled: true,
    adsRewardedEnabled: true,
    adsFrequency: 3,
    maxDailyAds: 10,

    // === FITUR BERBAYAR (PREMIUM) ===
    premiumEnabled: true,
    vipSystemEnabled: true,
    coinSystemEnabled: true,
    vipEpisodeEnabled: true,
    subscriptionEnabled: true,

    // === MONETIZATION ===
    coinPricePerEpisode: 10,
    dailySpinEnabled: true,
    dailyCheckInEnabled: true,
    freeCoinsOnRegister: 100,

    // === VIP PRICING (dalam IDR) ===
    vipMonthlyPrice: 49000,
    vipYearlyPrice: 490000,
};

// GET /api/settings
export async function GET() {
    try {
        const rows = await prisma.appSettings.findMany();
        const settings: Record<string, any> = {};
        for (const row of rows) {
            settings[row.key] = row.value;
        }

        return NextResponse.json({
            ...DEFAULT_SETTINGS,
            ...settings,
            // Convert specific types back
            maintenanceMode: settings.maintenanceMode === 'true',
            registrationsOpen: settings.registrationsOpen !== 'false',
            bannerRotationDays: parseInt(settings.bannerRotationDays || '2'),
            adsEnabled: settings.adsEnabled !== 'false',
            adsBannerEnabled: settings.adsBannerEnabled !== 'false',
            adsInterstitialEnabled: settings.adsInterstitialEnabled !== 'false',
            adsRewardedEnabled: settings.adsRewardedEnabled !== 'false',
            adsFrequency: parseInt(settings.adsFrequency || '3'),
            maxDailyAds: parseInt(settings.maxDailyAds || '10'),
            premiumEnabled: settings.premiumEnabled !== 'false',
            vipSystemEnabled: settings.vipSystemEnabled !== 'false',
            coinSystemEnabled: settings.coinSystemEnabled !== 'false',
            vipEpisodeEnabled: settings.vipEpisodeEnabled !== 'false',
            subscriptionEnabled: settings.subscriptionEnabled !== 'false',
            coinPricePerEpisode: parseInt(settings.coinPricePerEpisode || '10'),
            freeCoinsOnRegister: parseInt(settings.freeCoinsOnRegister || '100'),
            vipMonthlyPrice: parseInt(settings.vipMonthlyPrice || '49000'),
            vipYearlyPrice: parseInt(settings.vipYearlyPrice || '490000'),
        });
    } catch (error) {
        console.error('Settings GET Error:', error);
        return NextResponse.json(DEFAULT_SETTINGS, { status: 500 });
    }
}

// POST /api/settings
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const now = Math.floor(Date.now() / 1000);

        // Filter keys and update
        const updates = [];
        for (const key of Object.keys(DEFAULT_SETTINGS)) {
            if (body[key] !== undefined) {
                updates.push(
                    prisma.appSettings.upsert({
                        where: { key },
                        update: { value: String(body[key]), updatedAt: now },
                        create: { key, value: String(body[key]), updatedAt: now },
                    })
                );
            }
        }

        await prisma.$transaction(updates);

        return NextResponse.json({ success: true, message: 'Settings saved' });
    } catch (error) {
        console.error('Settings POST Error:', error);
        return NextResponse.json({ message: 'Failed to save settings' }, { status: 500 });
    }
}

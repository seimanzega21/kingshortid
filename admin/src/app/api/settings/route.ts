import { NextRequest, NextResponse } from 'next/server';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { join } from 'path';

const SETTINGS_FILE = join(process.cwd(), 'config', 'settings.json');

// Ensure config dir exists
async function ensureConfigDir() {
    try {
        await mkdir(join(process.cwd(), 'config'), { recursive: true });
    } catch { }
}

const DEFAULT_SETTINGS = {
    // Basic
    appName: "KingShort",
    appDescription: "Platform Drama Pendek Terbaik",
    maintenanceMode: false,
    registrationsOpen: true,

    // Localization
    currency: "IDR",
    language: "id",

    // === IKLAN (ADS) ===
    adsEnabled: true,                    // Master switch untuk semua iklan
    adsBannerEnabled: true,              // Banner ads di bawah layar
    adsInterstitialEnabled: true,        // Full-screen ads antar episode
    adsRewardedEnabled: true,            // Rewarded ads untuk koin
    adsFrequency: 3,                     // Tampilkan iklan setiap X episode
    maxDailyAds: 10,                     // Maksimal iklan per hari per user

    // === FITUR BERBAYAR (PREMIUM) ===
    premiumEnabled: true,                // Master switch fitur premium
    vipSystemEnabled: true,              // VIP membership system
    coinSystemEnabled: true,             // Sistem koin
    vipEpisodeEnabled: true,             // Episode khusus VIP
    subscriptionEnabled: true,           // Langganan bulanan

    // === MONETIZATION ===
    coinPricePerEpisode: 10,             // Harga unlock episode dalam koin
    dailySpinEnabled: true,              // Daily spin wheel
    dailyCheckInEnabled: true,           // Daily check-in reward
    freeCoinsOnRegister: 100,            // Koin gratis saat daftar

    // === VIP PRICING (dalam IDR) ===
    vipMonthlyPrice: 49000,
    vipYearlyPrice: 490000,
};


// GET /api/settings
export async function GET() {
    try {
        await ensureConfigDir();
        try {
            const data = await readFile(SETTINGS_FILE, 'utf-8');
            return NextResponse.json(JSON.parse(data));
        } catch (err) {
            // File doesn't exist, return defaults
            return NextResponse.json(DEFAULT_SETTINGS);
        }
    } catch (error) {
        return NextResponse.json(DEFAULT_SETTINGS, { status: 500 });
    }
}

// POST /api/settings
export async function POST(request: NextRequest) {
    try {
        await ensureConfigDir();
        const body = await request.json();

        // Merge with existing or defaults
        let current = DEFAULT_SETTINGS;
        try {
            const data = await readFile(SETTINGS_FILE, 'utf-8');
            current = JSON.parse(data);
        } catch { }

        const newSettings = { ...current, ...body };

        await writeFile(SETTINGS_FILE, JSON.stringify(newSettings, null, 2));

        return NextResponse.json(newSettings);
    } catch (error) {
        return NextResponse.json({ message: 'Failed to save settings' }, { status: 500 });
    }
}

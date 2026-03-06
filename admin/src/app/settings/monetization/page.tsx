"use client";

import { useState, useEffect } from "react";
import {
    Save,
    Wallet,
    Megaphone,
    Crown,
    Coins,
    Loader2
} from "lucide-react";
import { toast } from "sonner";

interface CoinPackage {
    id: string;
    coins: number;
    price: number;
    bonus: number;
    label: string;
}

interface MonetizationSettings {
    // Ads
    adsEnabled: boolean;
    adsBannerEnabled: boolean;
    adsInterstitialEnabled: boolean;
    adsRewardedEnabled: boolean;
    adsFrequency: number;
    maxDailyAds: number;
    // Premium
    premiumEnabled: boolean;
    vipSystemEnabled: boolean;
    coinSystemEnabled: boolean;
    vipEpisodeEnabled: boolean;
    subscriptionEnabled: boolean;
    dailySpinEnabled: boolean;
    dailyCheckInEnabled: boolean;
    coinPricePerEpisode: number;
    freeCoinsOnRegister: number;
    vipMonthlyPrice: number;
    vipYearlyPrice: number;
}

export default function MonetizationPage() {
    const [activeTab, setActiveTab] = useState("coins");
    const [packages, setPackages] = useState<CoinPackage[]>([]);
    const [settings, setSettings] = useState<MonetizationSettings | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [packagesRes, settingsRes] = await Promise.all([
                fetch("/api/finance/packages"),
                fetch("/api/settings")
            ]);
            const packagesData = await packagesRes.json();
            const settingsData = await settingsRes.json();

            if (Array.isArray(packagesData)) setPackages(packagesData);
            setSettings(settingsData);
        } catch (error) {
            console.error("Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        const toastId = toast.loading("Menyimpan...");
        try {
            // Save packages
            await fetch("/api/finance/packages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(packages)
            });

            // Save settings
            await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings)
            });

            toast.success("Tersimpan!", { id: toastId });
        } catch {
            toast.error("Gagal menyimpan", { id: toastId });
        }
    };

    const updatePackage = (index: number, field: string, value: any) => {
        const newPackages = [...packages];
        newPackages[index] = { ...newPackages[index], [field]: value };
        setPackages(newPackages);
    };

    const updateSetting = (key: keyof MonetizationSettings, value: any) => {
        if (settings) {
            setSettings({ ...settings, [key]: value });
        }
    };

    const Toggle = ({ enabled, onChange }: { enabled: boolean; onChange: () => void }) => (
        <div
            onClick={onChange}
            className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${enabled ? 'bg-purple-600' : 'bg-zinc-700'}`}
        >
            <div className={`w-4 h-4 rounded-full bg-white transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0'}`} />
        </div>
    );

    const ToggleRow = ({ title, desc, enabled, onChange }: { title: string; desc: string; enabled: boolean; onChange: () => void }) => (
        <div className="flex items-center justify-between py-3 border-b border-zinc-800 last:border-0">
            <div>
                <p className="text-white font-medium text-sm">{title}</p>
                <p className="text-xs text-zinc-500">{desc}</p>
            </div>
            <Toggle enabled={enabled} onChange={onChange} />
        </div>
    );

    if (loading || !settings) {
        return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-purple-500" size={40} /></div>;
    }

    return (
        <div className="p-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Monetisasi</h1>
                    <p className="text-zinc-400 mt-1">Kelola iklan, paket koin, dan fitur premium.</p>
                </div>
                <button onClick={handleSave} className="px-6 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors font-bold flex items-center gap-2">
                    <Save size={18} />
                    Simpan Perubahan
                </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-zinc-800">
                {[
                    { id: 'coins', label: 'Ekonomi Koin', icon: Wallet },
                    { id: 'ads', label: 'Iklan', icon: Megaphone },
                    { id: 'premium', label: 'Premium & VIP', icon: Crown },
                ].map(tab => (
                    <button
                        key={tab.id}
                        className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab === tab.id ? 'border-purple-500 text-white' : 'border-transparent text-zinc-400 hover:text-zinc-300'}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <tab.icon size={18} />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* === TAB EKONOMI KOIN === */}
            {activeTab === 'coins' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-4">
                        <h3 className="text-white font-semibold text-lg">Daftar Paket Koin</h3>
                        <p className="text-zinc-400 text-sm">Atur harga dan bonus untuk setiap paket top-up.</p>

                        <div className="space-y-4">
                            {packages.map((pkg, i) => (
                                <div key={i} className="bg-zinc-900 p-4 rounded-lg flex gap-4 items-end border border-zinc-800">
                                    <div className="flex-1 space-y-1">
                                        <label className="text-xs text-zinc-500">Label</label>
                                        <input value={pkg.label} onChange={(e) => updatePackage(i, 'label', e.target.value)}
                                            className="w-full bg-black border border-zinc-700 rounded px-2 py-1 text-sm text-white" />
                                    </div>
                                    <div className="w-24 space-y-1">
                                        <label className="text-xs text-zinc-500">Coins</label>
                                        <input type="number" value={pkg.coins} onChange={(e) => updatePackage(i, 'coins', parseInt(e.target.value))}
                                            className="w-full bg-black border border-zinc-700 rounded px-2 py-1 text-sm text-yellow-500 font-bold" />
                                    </div>
                                    <div className="w-24 space-y-1">
                                        <label className="text-xs text-zinc-500">Bonus</label>
                                        <input type="number" value={pkg.bonus} onChange={(e) => updatePackage(i, 'bonus', parseInt(e.target.value))}
                                            className="w-full bg-black border border-zinc-700 rounded px-2 py-1 text-sm text-green-500" />
                                    </div>
                                    <div className="w-32 space-y-1">
                                        <label className="text-xs text-zinc-500">Price (IDR)</label>
                                        <input type="number" value={pkg.price} onChange={(e) => updatePackage(i, 'price', parseInt(e.target.value))}
                                            className="w-full bg-black border border-zinc-700 rounded px-2 py-1 text-sm text-white" />
                                    </div>
                                </div>
                            ))}
                            <button
                                onClick={() => setPackages([...packages, { id: `p${Date.now()}`, coins: 100, price: 10000, bonus: 0, label: 'New Package' }])}
                                className="w-full py-2 border border-dashed border-zinc-700 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-900 transition-colors">
                                + Tambah Paket
                            </button>
                        </div>
                    </div>

                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <h3 className="text-white font-semibold text-lg mb-4">Preview di Aplikasi</h3>
                        <div className="space-y-2">
                            {packages.map((pkg, i) => (
                                <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-zinc-800 border border-zinc-700">
                                    <div className="flex items-center gap-3">
                                        <div className="h-8 w-8 rounded-full bg-yellow-500/20 flex items-center justify-center text-yellow-500">
                                            <Coins size={16} />
                                        </div>
                                        <div>
                                            <p className="text-white font-bold text-sm">{pkg.coins + pkg.bonus} Koin</p>
                                            <p className="text-xs text-zinc-400">{pkg.label}</p>
                                        </div>
                                    </div>
                                    <div className="bg-purple-600 px-3 py-1 rounded-md text-white text-xs font-bold">
                                        Rp {pkg.price.toLocaleString()}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* === TAB IKLAN === */}
            {activeTab === 'ads' && (
                <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 max-w-2xl">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-yellow-500/10 rounded-lg text-yellow-500"><Megaphone size={20} /></div>
                        <h3 className="text-lg font-bold text-white">Pengaturan Iklan</h3>
                    </div>
                    <ToggleRow title="🎯 Master Iklan" desc="ON/OFF semua iklan di aplikasi" enabled={settings.adsEnabled} onChange={() => updateSetting('adsEnabled', !settings.adsEnabled)} />
                    {settings.adsEnabled && (
                        <>
                            <ToggleRow title="Banner Ads" desc="Iklan banner di bawah layar" enabled={settings.adsBannerEnabled} onChange={() => updateSetting('adsBannerEnabled', !settings.adsBannerEnabled)} />
                            <ToggleRow title="Interstitial Ads" desc="Iklan fullscreen antar episode" enabled={settings.adsInterstitialEnabled} onChange={() => updateSetting('adsInterstitialEnabled', !settings.adsInterstitialEnabled)} />
                            <ToggleRow title="Rewarded Ads" desc="Iklan untuk mendapat koin gratis" enabled={settings.adsRewardedEnabled} onChange={() => updateSetting('adsRewardedEnabled', !settings.adsRewardedEnabled)} />
                            <div className="pt-4 mt-4 border-t border-zinc-800 space-y-4">
                                <div>
                                    <label className="text-sm text-zinc-400">Frekuensi Iklan (setiap X episode)</label>
                                    <input type="number" min={1} max={20} value={settings.adsFrequency ?? 5}
                                        onChange={(e) => updateSetting('adsFrequency', parseInt(e.target.value) || 5)}
                                        className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white" />
                                    <p className="text-xs text-zinc-600 mt-1">Interstitial muncul setiap {settings.adsFrequency ?? 5} episode ditonton</p>
                                </div>
                                <div>
                                    <label className="text-sm text-zinc-400">Maks Iklan per Hari</label>
                                    <input type="number" min={1} max={50} value={settings.maxDailyAds ?? 10}
                                        onChange={(e) => updateSetting('maxDailyAds', parseInt(e.target.value) || 10)}
                                        className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white" />
                                    <p className="text-xs text-zinc-600 mt-1">Batas iklan yang ditampilkan per user per hari</p>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* === TAB PREMIUM & VIP === */}
            {activeTab === 'premium' && (
                <div className="space-y-6 max-w-2xl">
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-amber-500/10 rounded-lg text-amber-500"><Crown size={20} /></div>
                            <h3 className="text-lg font-bold text-white">Fitur Premium</h3>
                        </div>
                        <ToggleRow title="👑 Master Premium" desc="ON/OFF semua fitur berbayar" enabled={settings.premiumEnabled} onChange={() => updateSetting('premiumEnabled', !settings.premiumEnabled)} />
                        {settings.premiumEnabled && (
                            <>
                                <ToggleRow title="VIP Membership" desc="Langganan VIP bulanan/tahunan" enabled={settings.vipSystemEnabled} onChange={() => updateSetting('vipSystemEnabled', !settings.vipSystemEnabled)} />
                                <ToggleRow title="Sistem Koin" desc="Pembelian dan penggunaan koin" enabled={settings.coinSystemEnabled} onChange={() => updateSetting('coinSystemEnabled', !settings.coinSystemEnabled)} />
                                <ToggleRow title="Episode VIP" desc="Episode berbayar khusus VIP" enabled={settings.vipEpisodeEnabled} onChange={() => updateSetting('vipEpisodeEnabled', !settings.vipEpisodeEnabled)} />
                                <ToggleRow title="Subscription Plans" desc="Paket langganan Premium/VIP" enabled={settings.subscriptionEnabled} onChange={() => updateSetting('subscriptionEnabled', !settings.subscriptionEnabled)} />
                            </>
                        )}
                    </div>

                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4">🎮 Gamifikasi</h3>
                        <ToggleRow title="Daily Spin Wheel" desc="Spin harian untuk koin gratis" enabled={settings.dailySpinEnabled} onChange={() => updateSetting('dailySpinEnabled', !settings.dailySpinEnabled)} />
                        <ToggleRow title="Daily Check-In" desc="Hadiah login berturut-turut" enabled={settings.dailyCheckInEnabled} onChange={() => updateSetting('dailyCheckInEnabled', !settings.dailyCheckInEnabled)} />
                    </div>

                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-4">
                        <h3 className="text-lg font-bold text-white mb-2">💰 Pengaturan Harga</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-zinc-400">Harga Episode (Koin)</label>
                                <input type="number" value={settings.coinPricePerEpisode} onChange={(e) => updateSetting('coinPricePerEpisode', parseInt(e.target.value))}
                                    className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white" />
                            </div>
                            <div>
                                <label className="text-sm text-zinc-400">Koin Gratis (Daftar)</label>
                                <input type="number" value={settings.freeCoinsOnRegister} onChange={(e) => updateSetting('freeCoinsOnRegister', parseInt(e.target.value))}
                                    className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-zinc-400">VIP Bulanan (IDR)</label>
                                <input type="number" value={settings.vipMonthlyPrice} onChange={(e) => updateSetting('vipMonthlyPrice', parseInt(e.target.value))}
                                    className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white" />
                            </div>
                            <div>
                                <label className="text-sm text-zinc-400">VIP Tahunan (IDR)</label>
                                <input type="number" value={settings.vipYearlyPrice} onChange={(e) => updateSetting('vipYearlyPrice', parseInt(e.target.value))}
                                    className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white" />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

"use client";

import { useState, useEffect } from "react";
import {
    Save,
    Wallet,
    Megaphone,
    Crown,
    Coins,
    Loader2,
    Timer,
    Eye,
    Gift,
    Smartphone,
    Copy,
    Check,
    Info
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
    // Extended ad settings
    interstitialCloseDelay: number;
    rewardedCoinsAmount: number;
    bannerPosition: string;
    // Ad Unit IDs
    adUnitBanner: string;
    adUnitInterstitial: string;
    adUnitRewarded: string;
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

    function HealthCard({ label, value, color, icon }: { label: string; value: number; color: string; icon: string }) {
        const colors: Record<string, string> = {
            emerald: 'border-emerald-500/20 bg-emerald-500/5',
            amber: 'border-amber-500/20 bg-amber-500/5',
            red: 'border-red-500/20 bg-red-500/5',
            zinc: 'border-zinc-700 bg-zinc-800/50',
        };
        const textColors: Record<string, string> = {
            emerald: 'text-emerald-400',
            amber: 'text-amber-400',
            red: 'text-red-400',
            zinc: 'text-zinc-400',
        };
        return (
            <div className={`rounded-lg border p-3 ${colors[color] || colors.zinc}`}>
                <div className="flex items-center justify-between">
                    <span className="text-lg">{icon}</span>
                    <span className={`text-xl font-bold ${textColors[color] || textColors.zinc}`}>{value}</span>
                </div>
                <p className="text-[11px] text-zinc-500 mt-1">{label}</p>
            </div>
        );
    }

    function AdUnitIdCard({ settings, updateSetting }: { settings: MonetizationSettings; updateSetting: (key: keyof MonetizationSettings, value: any) => void }) {
        const [copied, setCopied] = useState<string | null>(null);

        const handleCopy = (value: string, key: string) => {
            navigator.clipboard.writeText(value);
            setCopied(key);
            setTimeout(() => setCopied(null), 2000);
        };

        const adUnits = [
            { key: 'adUnitBanner' as const, label: 'Banner Ad Unit ID', color: 'blue', default: 'ca-app-pub-6488135194537188/9618891521' },
            { key: 'adUnitInterstitial' as const, label: 'Interstitial Ad Unit ID', color: 'amber', default: 'ca-app-pub-6488135194537188/1033626745' },
            { key: 'adUnitRewarded' as const, label: 'Rewarded Ad Unit ID', color: 'emerald', default: 'ca-app-pub-6488135194537188/1035626745' },
        ];

        return (
            <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <h4 className="text-white font-semibold flex items-center gap-2"><Smartphone size={18} className="text-zinc-400" /> Ad Unit IDs (AdMob)</h4>
                    <span className="text-[10px] text-zinc-600 bg-zinc-900 px-2 py-1 rounded">Google AdMob Console</span>
                </div>
                <div className="space-y-3">
                    {adUnits.map(unit => {
                        const value = (settings[unit.key] as string) || unit.default;
                        return (
                            <div key={unit.key} className="flex items-center gap-3">
                                <div className={`w-2 h-2 rounded-full bg-${unit.color}-500 flex-shrink-0`} />
                                <div className="flex-1">
                                    <label className="text-[11px] text-zinc-500 uppercase tracking-wide">{unit.label}</label>
                                    <div className="flex gap-2 mt-1">
                                        <input value={value}
                                            onChange={(e) => updateSetting(unit.key, e.target.value)}
                                            className="flex-1 bg-black border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-300 font-mono outline-none focus:border-purple-500"
                                            placeholder="ca-app-pub-xxxxx/xxxxx" />
                                        <button onClick={() => handleCopy(value, unit.key)}
                                            className="px-2 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 transition-colors flex-shrink-0"
                                            title="Copy">
                                            {copied === unit.key ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
                <p className="text-[10px] text-zinc-600 mt-4 flex items-center gap-1">
                    <Info size={10} /> ID ini diambil dari Google AdMob Console. Perubahan memerlukan build ulang aplikasi.
                </p>
            </div>
        );
    }

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
                <div className="space-y-6 max-w-4xl">
                    {/* Master Switch */}
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 bg-yellow-500/10 rounded-xl text-yellow-500"><Megaphone size={22} /></div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">🎯 Master Iklan</h3>
                                    <p className="text-sm text-zinc-500">ON/OFF semua iklan di aplikasi</p>
                                </div>
                            </div>
                            <Toggle enabled={settings.adsEnabled} onChange={() => updateSetting('adsEnabled', !settings.adsEnabled)} />
                        </div>
                    </div>

                    {settings.adsEnabled && (
                        <>
                            {/* Ad Type Cards */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                {/* Banner */}
                                <div className={`bg-[#121212] border rounded-xl p-5 transition-all ${settings.adsBannerEnabled ? 'border-blue-500/30 shadow-lg shadow-blue-500/5' : 'border-zinc-800'}`}>
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <div className="p-1.5 bg-blue-500/10 rounded-lg text-blue-400"><Smartphone size={16} /></div>
                                            <h4 className="font-semibold text-white text-sm">Banner</h4>
                                        </div>
                                        <Toggle enabled={settings.adsBannerEnabled} onChange={() => updateSetting('adsBannerEnabled', !settings.adsBannerEnabled)} />
                                    </div>
                                    <p className="text-xs text-zinc-500 mb-3">Iklan banner di bawah layar, muncul terus saat user browsing.</p>
                                    {settings.adsBannerEnabled && (
                                        <div>
                                            <label className="text-[11px] text-zinc-500 uppercase tracking-wide">Posisi</label>
                                            <select value={settings.bannerPosition || 'bottom'}
                                                onChange={(e) => updateSetting('bannerPosition', e.target.value)}
                                                className="w-full mt-1 bg-black border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500">
                                                <option value="bottom">Bawah Layar</option>
                                                <option value="top">Atas Layar</option>
                                            </select>
                                        </div>
                                    )}
                                </div>

                                {/* Interstitial */}
                                <div className={`bg-[#121212] border rounded-xl p-5 transition-all ${settings.adsInterstitialEnabled ? 'border-amber-500/30 shadow-lg shadow-amber-500/5' : 'border-zinc-800'}`}>
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <div className="p-1.5 bg-amber-500/10 rounded-lg text-amber-400"><Eye size={16} /></div>
                                            <h4 className="font-semibold text-white text-sm">Interstitial</h4>
                                        </div>
                                        <Toggle enabled={settings.adsInterstitialEnabled} onChange={() => updateSetting('adsInterstitialEnabled', !settings.adsInterstitialEnabled)} />
                                    </div>
                                    <p className="text-xs text-zinc-500 mb-3">Iklan fullscreen yang muncul antar episode.</p>
                                    {settings.adsInterstitialEnabled && (
                                        <div className="space-y-3">
                                            <div>
                                                <label className="text-[11px] text-zinc-500 uppercase tracking-wide flex items-center gap-1"><Timer size={10} /> Delay Close (detik)</label>
                                                <input type="number" min={0} max={30} value={settings.interstitialCloseDelay ?? 5}
                                                    onChange={(e) => updateSetting('interstitialCloseDelay', parseInt(e.target.value) || 5)}
                                                    className="w-full mt-1 bg-black border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
                                                <p className="text-[10px] text-zinc-600 mt-1">User harus tunggu {settings.interstitialCloseDelay ?? 5}s sebelum bisa skip</p>
                                            </div>
                                            <div>
                                                <label className="text-[11px] text-zinc-500 uppercase tracking-wide">Frekuensi (per X episode)</label>
                                                <input type="number" min={1} max={20} value={settings.adsFrequency ?? 5}
                                                    onChange={(e) => updateSetting('adsFrequency', parseInt(e.target.value) || 5)}
                                                    className="w-full mt-1 bg-black border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-amber-500" />
                                                <p className="text-[10px] text-zinc-600 mt-1">Muncul setiap {settings.adsFrequency ?? 5} episode</p>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Rewarded */}
                                <div className={`bg-[#121212] border rounded-xl p-5 transition-all ${settings.adsRewardedEnabled ? 'border-emerald-500/30 shadow-lg shadow-emerald-500/5' : 'border-zinc-800'}`}>
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <div className="p-1.5 bg-emerald-500/10 rounded-lg text-emerald-400"><Gift size={16} /></div>
                                            <h4 className="font-semibold text-white text-sm">Rewarded</h4>
                                        </div>
                                        <Toggle enabled={settings.adsRewardedEnabled} onChange={() => updateSetting('adsRewardedEnabled', !settings.adsRewardedEnabled)} />
                                    </div>
                                    <p className="text-xs text-zinc-500 mb-3">Iklan opsional, user pilih nonton untuk dapat koin.</p>
                                    {settings.adsRewardedEnabled && (
                                        <div>
                                            <label className="text-[11px] text-zinc-500 uppercase tracking-wide flex items-center gap-1"><Coins size={10} /> Reward (koin)</label>
                                            <input type="number" min={1} max={100} value={settings.rewardedCoinsAmount ?? 10}
                                                onChange={(e) => updateSetting('rewardedCoinsAmount', parseInt(e.target.value) || 10)}
                                                className="w-full mt-1 bg-black border border-zinc-700 rounded-lg px-3 py-2 text-sm text-yellow-500 font-bold outline-none focus:border-emerald-500" />
                                            <p className="text-[10px] text-zinc-600 mt-1">Koin yang didapat per iklan</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Global Ad Limits */}
                            <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                                <h4 className="text-white font-semibold mb-4 flex items-center gap-2"><Timer size={18} className="text-zinc-400" /> Batas Global</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="text-sm text-zinc-400">Maks Iklan per Hari</label>
                                        <input type="number" min={1} max={50} value={settings.maxDailyAds ?? 10}
                                            onChange={(e) => updateSetting('maxDailyAds', parseInt(e.target.value) || 10)}
                                            className="w-full mt-2 bg-black border border-zinc-700 rounded-lg px-4 py-2 text-white outline-none focus:border-purple-500" />
                                        <p className="text-xs text-zinc-600 mt-1">Batas total semua jenis iklan per user per hari</p>
                                    </div>
                                    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800">
                                        <p className="text-xs text-zinc-500 mb-2 flex items-center gap-1"><Info size={12} /> Ringkasan Konfigurasi</p>
                                        <div className="space-y-1.5">
                                            <div className="flex justify-between text-xs">
                                                <span className="text-zinc-400">Banner</span>
                                                <span className={settings.adsBannerEnabled ? 'text-blue-400' : 'text-zinc-600'}>{settings.adsBannerEnabled ? '✅ Aktif' : '❌ Mati'}</span>
                                            </div>
                                            <div className="flex justify-between text-xs">
                                                <span className="text-zinc-400">Interstitial</span>
                                                <span className={settings.adsInterstitialEnabled ? 'text-amber-400' : 'text-zinc-600'}>{settings.adsInterstitialEnabled ? `✅ Setiap ${settings.adsFrequency} ep · ${settings.interstitialCloseDelay ?? 5}s skip` : '❌ Mati'}</span>
                                            </div>
                                            <div className="flex justify-between text-xs">
                                                <span className="text-zinc-400">Rewarded</span>
                                                <span className={settings.adsRewardedEnabled ? 'text-emerald-400' : 'text-zinc-600'}>{settings.adsRewardedEnabled ? `✅ ${settings.rewardedCoinsAmount ?? 10} koin/iklan` : '❌ Mati'}</span>
                                            </div>
                                            <div className="flex justify-between text-xs pt-1 border-t border-zinc-800">
                                                <span className="text-zinc-400">Maks/hari</span>
                                                <span className="text-white font-bold">{settings.maxDailyAds ?? 10}x</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Ad Unit IDs */}
                            <AdUnitIdCard
                                settings={settings}
                                updateSetting={updateSetting}
                            />
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

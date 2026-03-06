"use client";

import { useEffect, useState } from "react";
import {
    Settings as SettingsIcon,
    Shield,
    Save,
    ChevronRight,
    User,
    FileText,
    Bell,
    Lock,
    Loader2,
    Globe,
    Mail,
    Phone,
} from "lucide-react";
import { toast } from "sonner";

interface AppSettings {
    appName: string;
    appDescription: string;
    maintenanceMode: boolean;
    registrationsOpen: boolean;
    language: string;
    currency: string;
    // Legal
    termsUrl: string;
    privacyUrl: string;
    contactEmail: string;
    contactPhone: string;
    // Security
    maxLoginAttempts: number;
    sessionTimeout: number;
    twoFactorEnabled: boolean;
}

const Toggle = ({ enabled, onChange }: { enabled: boolean; onChange: () => void }) => (
    <div
        onClick={onChange}
        className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${enabled ? 'bg-purple-600' : 'bg-zinc-700'}`}
    >
        <div className={`w-4 h-4 rounded-full bg-white transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0'}`} />
    </div>
);

const ToggleRow = ({ title, desc, enabled, onChange }: { title: string; desc: string; enabled: boolean; onChange: () => void }) => (
    <div className="flex items-center justify-between py-4 border-b border-zinc-800 last:border-0">
        <div>
            <p className="text-white font-medium">{title}</p>
            <p className="text-sm text-zinc-400">{desc}</p>
        </div>
        <Toggle enabled={enabled} onChange={onChange} />
    </div>
);

const InputField = ({ label, value, onChange, type = "text", placeholder = "" }: { label: string; value: any; onChange: (v: any) => void; type?: string; placeholder?: string }) => (
    <div className="space-y-1.5">
        <label className="text-sm text-zinc-400">{label}</label>
        <input
            type={type}
            value={value || ''}
            placeholder={placeholder}
            onChange={(e) => onChange(type === 'number' ? parseInt(e.target.value) || 0 : e.target.value)}
            className="w-full bg-[#18181b] border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
        />
    </div>
);

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState("general");
    const [settings, setSettings] = useState<AppSettings | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await fetch("/api/settings");
                const data = await res.json();
                setSettings({
                    appName: data.appName || "KingShort",
                    appDescription: data.appDescription || "",
                    maintenanceMode: data.maintenanceMode || false,
                    registrationsOpen: data.registrationsOpen ?? true,
                    language: data.language || "id",
                    currency: data.currency || "IDR",
                    termsUrl: data.termsUrl || "",
                    privacyUrl: data.privacyUrl || "",
                    contactEmail: data.contactEmail || "",
                    contactPhone: data.contactPhone || "",
                    maxLoginAttempts: data.maxLoginAttempts || 5,
                    sessionTimeout: data.sessionTimeout || 24,
                    twoFactorEnabled: data.twoFactorEnabled || false,
                });
            } catch (err) {
                console.error("Failed to load settings");
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const updateSetting = (key: keyof AppSettings, value: any) => {
        if (settings) {
            setSettings({ ...settings, [key]: value });
        }
    };

    const handleSave = async () => {
        const toastId = toast.loading("Menyimpan...");
        try {
            const res = await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings)
            });
            if (!res.ok) throw new Error("Failed");
            toast.success("Tersimpan!", { id: toastId });
        } catch {
            toast.error("Gagal menyimpan", { id: toastId });
        }
    };

    if (loading || !settings) {
        return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-purple-500" size={40} /></div>;
    }

    return (
        <div className="min-h-screen bg-[#09090b] p-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                    <span>Panel</span>
                    <ChevronRight size={14} />
                    <span className="text-white font-medium">Pengaturan Sistem</span>
                </div>
                <button onClick={handleSave} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2">
                    <Save size={18} /> Simpan
                </button>
            </div>

            <div>
                <h1 className="text-4xl font-bold tracking-tight text-white mb-2">Pengaturan Admin</h1>
                <p className="text-zinc-400">Kelola profil, legal, keamanan, dan pengaturan umum sistem.</p>
            </div>

            {/* 5 Tabs */}
            <div className="border-b border-zinc-800">
                <div className="flex gap-6 overflow-x-auto">
                    {[
                        { id: 'general', label: 'Umum', icon: SettingsIcon },
                        { id: 'profile', label: 'Profil Admin', icon: User },
                        { id: 'legal', label: 'Legal', icon: FileText },
                        { id: 'notifications', label: 'Notifikasi', icon: Bell },
                        { id: 'security', label: 'Keamanan', icon: Lock },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`pb-4 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${activeTab === tab.id ? 'border-purple-500 text-white' : 'border-transparent text-zinc-400 hover:text-zinc-300'}`}
                        >
                            <tab.icon size={16} />
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">

                    {/* === TAB UMUM === */}
                    {activeTab === 'general' && (
                        <>
                            <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-6">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500"><SettingsIcon size={20} /></div>
                                    <h3 className="text-lg font-bold text-white">Detail Platform</h3>
                                </div>
                                <div className="grid grid-cols-2 gap-6">
                                    <InputField label="Nama Platform" value={settings.appName} onChange={(v) => updateSetting('appName', v)} />
                                    <div className="space-y-1.5">
                                        <label className="text-sm text-zinc-400">Bahasa Default</label>
                                        <select
                                            value={settings.language}
                                            onChange={(e) => updateSetting('language', e.target.value)}
                                            className="w-full bg-[#18181b] border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                                        >
                                            <option value="id">Bahasa Indonesia</option>
                                            <option value="en">English</option>
                                        </select>
                                    </div>
                                </div>
                                <InputField label="Deskripsi Aplikasi" value={settings.appDescription} onChange={(v) => updateSetting('appDescription', v)} placeholder="Deskripsi singkat tentang aplikasi" />
                            </div>
                            <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                                <ToggleRow title="Mode Pemeliharaan" desc="Tutup akses publik sementara" enabled={settings.maintenanceMode} onChange={() => updateSetting('maintenanceMode', !settings.maintenanceMode)} />
                                <ToggleRow title="Registrasi Terbuka" desc="Izinkan pengguna baru mendaftar" enabled={settings.registrationsOpen} onChange={() => updateSetting('registrationsOpen', !settings.registrationsOpen)} />
                            </div>
                        </>
                    )}

                    {/* === TAB PROFIL ADMIN === */}
                    {activeTab === 'profile' && (
                        <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500"><User size={20} /></div>
                                <h3 className="text-lg font-bold text-white">Profil Administrator</h3>
                            </div>
                            <div className="flex items-center gap-6">
                                <div className="w-20 h-20 rounded-full bg-zinc-800 flex items-center justify-center">
                                    <User size={40} className="text-zinc-500" />
                                </div>
                                <div>
                                    <p className="text-white font-bold">Admin User</p>
                                    <p className="text-zinc-400 text-sm">admin@kingshort.com</p>
                                    <button className="text-purple-500 text-sm mt-2 hover:underline">Ganti Foto</button>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-800">
                                <InputField label="Nama Lengkap" value="Admin User" onChange={() => { }} />
                                <InputField label="Email" value="admin@kingshort.com" onChange={() => { }} type="email" />
                            </div>
                            <button className="text-purple-500 text-sm hover:underline">Ubah Password →</button>
                        </div>
                    )}

                    {/* === TAB LEGAL === */}
                    {activeTab === 'legal' && (
                        <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-green-500/10 rounded-lg text-green-500"><FileText size={20} /></div>
                                <h3 className="text-lg font-bold text-white">Dokumen Legal</h3>
                            </div>
                            <InputField label="URL Syarat & Ketentuan" value={settings.termsUrl} onChange={(v) => updateSetting('termsUrl', v)} placeholder="https://example.com/terms" />
                            <InputField label="URL Kebijakan Privasi" value={settings.privacyUrl} onChange={(v) => updateSetting('privacyUrl', v)} placeholder="https://example.com/privacy" />
                            <div className="pt-4 border-t border-zinc-800">
                                <h4 className="text-white font-medium mb-4">Informasi Kontak</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <InputField label="Email Dukungan" value={settings.contactEmail} onChange={(v) => updateSetting('contactEmail', v)} placeholder="support@example.com" />
                                    <InputField label="Telepon" value={settings.contactPhone} onChange={(v) => updateSetting('contactPhone', v)} placeholder="+62 xxx" />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* === TAB NOTIFIKASI === */}
                    {activeTab === 'notifications' && (
                        <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-4">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-orange-500/10 rounded-lg text-orange-500"><Bell size={20} /></div>
                                <h3 className="text-lg font-bold text-white">Pengaturan Notifikasi</h3>
                            </div>
                            <ToggleRow title="Email Notifikasi" desc="Terima notifikasi via email" enabled={true} onChange={() => { }} />
                            <ToggleRow title="Push Notifikasi Admin" desc="Notifikasi browser untuk aktivitas penting" enabled={true} onChange={() => { }} />
                            <ToggleRow title="Laporan Harian" desc="Ringkasan aktivitas setiap hari" enabled={false} onChange={() => { }} />
                            <ToggleRow title="Alert Keamanan" desc="Notifikasi login mencurigakan" enabled={true} onChange={() => { }} />
                        </div>
                    )}

                    {/* === TAB KEAMANAN === */}
                    {activeTab === 'security' && (
                        <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-red-500/10 rounded-lg text-red-500"><Lock size={20} /></div>
                                <h3 className="text-lg font-bold text-white">Pengaturan Keamanan</h3>
                            </div>
                            <ToggleRow title="Two-Factor Authentication" desc="Verifikasi 2 langkah untuk login admin" enabled={settings.twoFactorEnabled} onChange={() => updateSetting('twoFactorEnabled', !settings.twoFactorEnabled)} />
                            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-800">
                                <InputField label="Maks Percobaan Login" value={settings.maxLoginAttempts} onChange={(v) => updateSetting('maxLoginAttempts', v)} type="number" />
                                <InputField label="Timeout Sesi (jam)" value={settings.sessionTimeout} onChange={(v) => updateSetting('sessionTimeout', v)} type="number" />
                            </div>
                            <div className="pt-4 border-t border-zinc-800">
                                <button className="text-red-500 text-sm hover:underline">Logout Semua Sesi Aktif →</button>
                            </div>
                        </div>
                    )}

                    <button onClick={handleSave} className="w-full bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-bold flex items-center justify-center gap-2">
                        <Save size={16} /> Simpan Perubahan
                    </button>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <div className="bg-[#1a1528] rounded-xl p-6 border border-purple-500/20">
                        <div className="h-10 w-10 bg-purple-600 rounded-lg flex items-center justify-center mb-4 text-white"><Shield size={20} /></div>
                        <h3 className="text-lg font-bold text-white mb-2">Status Sistem</h3>
                        <p className="text-sm text-zinc-400">Semua layanan berjalan lancar.</p>
                        <div className="mt-4 pt-4 border-t border-purple-500/20 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-zinc-400">Database</span>
                                <span className="text-green-400">Online</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-zinc-400">Storage</span>
                                <span className="text-green-400">75% Free</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-zinc-400">API</span>
                                <span className="text-green-400">Healthy</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-4">
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Ringkasan</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-zinc-400 text-sm">Maintenance</span>
                                <span className={`text-sm font-bold ${settings.maintenanceMode ? 'text-yellow-400' : 'text-green-400'}`}>
                                    {settings.maintenanceMode ? 'ON' : 'OFF'}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-zinc-400 text-sm">Registrasi</span>
                                <span className={`text-sm font-bold ${settings.registrationsOpen ? 'text-green-400' : 'text-red-400'}`}>
                                    {settings.registrationsOpen ? 'BUKA' : 'TUTUP'}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-zinc-400 text-sm">2FA</span>
                                <span className={`text-sm font-bold ${settings.twoFactorEnabled ? 'text-green-400' : 'text-zinc-500'}`}>
                                    {settings.twoFactorEnabled ? 'AKTIF' : 'NONAKTIF'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

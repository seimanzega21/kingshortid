"use client";

import { MobileLayout } from "@/components/MobileLayout";
import { Settings, ChevronRight, History, Heart, User, Wallet, Bell, HelpCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";

interface UserData {
    id: string;
    email: string;
    name: string;
    avatar?: string;
    coins: number;
    vipStatus: boolean;
    vipExpiry?: string;
}

interface CoinBalance {
    balance: number;
    lifetimeEarned: number;
    lifetimeSpent: number;
}

export default function ProfilePage() {
    const [user, setUser] = useState<UserData | null>(null);
    const [coinBalance, setCoinBalance] = useState<CoinBalance | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const menuItems = [
        { label: "Riwayat Tontonan", icon: History, href: "/library?tab=history" },
        { label: "Daftar Tontonan", icon: Heart, href: "/library?tab=watchlist" },
        { label: "Notifikasi", icon: Bell, href: "/notifications" },
        { label: "Pengaturan", icon: Settings, href: "/settings" },
        { label: "Bantuan & Saran", icon: HelpCircle, href: "/help" },
    ];

    useEffect(() => {
        fetchUserData();
    }, []);

    const fetchUserData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch user profile
            const userResponse = await fetch('/api/auth/me');
            if (!userResponse.ok) throw new Error('Failed to fetch user data');
            const userData = await userResponse.json();
            setUser(userData);

            // Fetch coin balance
            const coinsResponse = await fetch('/api/coins/balance');
            if (!coinsResponse.ok) throw new Error('Failed to fetch coin balance');
            const coinsData = await coinsResponse.json();
            setCoinBalance(coinsData);

        } catch (err) {
            console.error('Error fetching profile:', err);
            setError('Gagal memuat data profil');
        } finally {
            setLoading(false);
        }
    };

    const getShortId = (id: string) => {
        return id.substring(0, 8).toUpperCase();
    };

    if (loading) {
        return (
            <MobileLayout>
                <div className="min-h-screen bg-black text-white flex items-center justify-center">
                    <div className="text-center">
                        <Loader2 className="w-10 h-10 animate-spin text-yellow-500 mx-auto mb-4" />
                        <p className="text-gray-400 text-sm">Memuat profil...</p>
                    </div>
                </div>
            </MobileLayout>
        );
    }

    if (error || !user) {
        return (
            <MobileLayout>
                <div className="min-h-screen bg-black text-white flex items-center justify-center px-6">
                    <div className="text-center">
                        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
                            <User className="w-8 h-8 text-red-500" />
                        </div>
                        <p className="text-red-400 text-sm mb-4">{error || 'Gagal memuat profil'}</p>
                        <button
                            onClick={fetchUserData}
                            className="text-yellow-500 hover:text-yellow-400 text-sm font-medium"
                        >
                            Coba lagi
                        </button>
                    </div>
                </div>
            </MobileLayout>
        );
    }

    return (
        <MobileLayout>
            <div className="min-h-screen bg-black text-white pb-24">

                {/* Header / User Info */}
                <div className="pt-12 px-6 pb-8 bg-gradient-to-b from-zinc-900 to-black">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-20 h-20 rounded-full bg-zinc-800 border-2 border-yellow-500 overflow-hidden relative">
                            {/* Avatar */}
                            {user.avatar ? (
                                <img
                                    src={user.avatar}
                                    alt={user.name}
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-yellow-500 to-yellow-600">
                                    <span className="text-2xl font-bold text-black">
                                        {user.name.charAt(0).toUpperCase()}
                                    </span>
                                </div>
                            )}
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold">{user.name}</h1>
                            <p className="text-gray-400 text-sm">ID: {getShortId(user.id)}</p>
                            <Link href="/edit-profile" className="text-xs text-yellow-500 hover:text-yellow-400 font-medium mt-1 inline-block">
                                Edit Profile
                            </Link>
                        </div>
                    </div>

                    {/* Wallet Card */}
                    <div className="bg-gradient-to-r from-yellow-600 to-yellow-400 rounded-2xl p-4 shadow-lg shadow-yellow-500/10 text-black">
                        <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                                <Wallet className="w-5 h-5 text-black" />
                                <span className="font-bold text-sm">Dompet Saya</span>
                            </div>
                            <button className="bg-black/20 hover:bg-black/30 backdrop-blur px-3 py-1 rounded-full text-xs font-bold transition-colors">
                                Top Up
                            </button>
                        </div>
                        <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-extrabold">
                                {coinBalance?.balance.toLocaleString() || user.coins.toLocaleString()}
                            </span>
                            <span className="text-sm font-semibold opacity-80">Koin</span>
                        </div>
                        {user.vipStatus && (
                            <div className="mt-2 bg-black/20 rounded-lg px-2 py-1 inline-block">
                                <span className="text-[10px] font-bold">⭐ VIP Member</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Menu List */}
                <div className="px-4 space-y-2">
                    {menuItems.map((item, i) => (
                        <Link
                            key={i}
                            href={item.href}
                            className="flex items-center justify-between p-4 bg-zinc-900/50 hover:bg-zinc-900 rounded-xl border border-zinc-900 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-zinc-800 rounded-lg text-yellow-500">
                                    <item.icon size={20} />
                                </div>
                                <span className="font-medium">{item.label}</span>
                            </div>
                            <ChevronRight size={18} className="text-gray-600" />
                        </Link>
                    ))}
                </div>

                {/* Version */}
                <div className="text-center mt-8 text-xs text-gray-600">
                    v1.0.0 King Shortid
                </div>

            </div>
        </MobileLayout>
    );
}

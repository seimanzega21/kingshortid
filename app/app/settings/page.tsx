"use client";

import { MobileLayout } from "@/components/MobileLayout";
import { ChevronLeft, Bell, Lock, Globe, Trash2, Moon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { clsx } from "clsx";

export default function SettingsPage() {
    const [notifications, setNotifications] = useState(true);
    const [darkMode, setDarkMode] = useState(true);

    return (
        <MobileLayout showNav={false}>
            <div className="min-h-screen bg-black text-white p-6">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/profile" className="p-2 -ml-2 text-gray-400 hover:text-white bg-zinc-900 rounded-full">
                        <ChevronLeft size={24} />
                    </Link>
                    <h1 className="text-xl font-bold">Pengaturan</h1>
                </div>

                <div className="space-y-6">

                    {/* Section: Umum */}
                    <section className="space-y-3">
                        <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider ml-1">Umum</h2>

                        <div className="bg-zinc-900 rounded-2xl overflow-hidden p-1">
                            <div className="flex items-center justify-between p-4 border-b border-zinc-800 last:border-0">
                                <div className="flex items-center gap-3">
                                    <Bell size={20} className="text-yellow-500" />
                                    <span className="font-medium">Notifikasi Push</span>
                                </div>
                                <button
                                    onClick={() => setNotifications(!notifications)}
                                    className={clsx("w-12 h-6 rounded-full relative transition-colors", notifications ? "bg-yellow-500" : "bg-zinc-700")}
                                >
                                    <div className={clsx("absolute top-1 w-4 h-4 rounded-full bg-white transition-all shadow", notifications ? "left-7" : "left-1")} />
                                </button>
                            </div>

                            <div className="flex items-center justify-between p-4">
                                <div className="flex items-center gap-3">
                                    <Moon size={20} className="text-yellow-500" />
                                    <span className="font-medium">Mode Gelap</span>
                                </div>
                                <button
                                    onClick={() => setDarkMode(!darkMode)}
                                    className={clsx("w-12 h-6 rounded-full relative transition-colors", darkMode ? "bg-yellow-500" : "bg-zinc-700")}
                                >
                                    <div className={clsx("absolute top-1 w-4 h-4 rounded-full bg-black transition-all shadow", darkMode ? "left-7" : "left-1")} />
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* Section: Akun */}
                    <section className="space-y-3">
                        <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider ml-1">Akun & Keamanan</h2>

                        <div className="bg-zinc-900 rounded-2xl overflow-hidden p-1">
                            <Link href="#" className="flex items-center justify-between p-4 border-b border-zinc-800 last:border-0 hover:bg-zinc-800 rounded-xl transition-colors">
                                <div className="flex items-center gap-3">
                                    <Lock size={20} className="text-gray-400" />
                                    <span className="font-medium">Ubah Password</span>
                                </div>
                                <ChevronLeft size={16} className="rotate-180 text-gray-600" />
                            </Link>

                            <Link href="#" className="flex items-center justify-between p-4 hover:bg-zinc-800 rounded-xl transition-colors">
                                <div className="flex items-center gap-3">
                                    <Globe size={20} className="text-gray-400" />
                                    <span className="font-medium">Bahasa</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-gray-500">Indonesia</span>
                                    <ChevronLeft size={16} className="rotate-180 text-gray-600" />
                                </div>
                            </Link>
                        </div>
                    </section>

                    {/* Section: Cache */}
                    <section className="space-y-3">
                        <div className="bg-zinc-900 rounded-2xl overflow-hidden p-1">
                            <button className="w-full flex items-center justify-between p-4 hover:bg-zinc-800 rounded-xl transition-colors text-red-500">
                                <div className="flex items-center gap-3">
                                    <Trash2 size={20} />
                                    <span className="font-medium">Hapus Cache</span>
                                </div>
                                <span className="text-xs font-bold bg-zinc-800 px-2 py-1 rounded text-gray-400">128 MB</span>
                            </button>
                        </div>
                    </section>

                    <div className="pt-8 text-center">
                        <button className="text-red-500 font-bold text-sm hover:underline">Keluar Akun</button>
                        <p className="mt-4 text-[10px] text-zinc-600">App Version 1.0.0 (Build 2024)</p>
                    </div>

                </div>
            </div>
        </MobileLayout>
    );
}

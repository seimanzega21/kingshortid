"use client";

import { useState, useEffect, useCallback } from "react";
import { RefreshCw, Wifi, Crown, UserX, Chrome, Clock } from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

interface OnlineUser {
    id: string;
    name: string;
    email: string;
    provider: string;
    isGuest: boolean;
    vipStatus: boolean;
    lastSeen: string | null;
}

export default function OnlineUsersPage() {
    const [users, setUsers] = useState<OnlineUser[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchOnlineUsers = useCallback(async () => {
        try {
            const res = await fetch("/api/users/online");
            if (res.ok) {
                const data = await res.json();
                setUsers(data.users || []);
                setTotal(data.total || 0);
            }
        } catch {
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchOnlineUsers();
    }, [fetchOnlineUsers]);

    useEffect(() => {
        if (!autoRefresh) return;
        const interval = setInterval(fetchOnlineUsers, 30000);
        return () => clearInterval(interval);
    }, [autoRefresh, fetchOnlineUsers]);

    const formatLastSeen = (dateStr: string | null) => {
        if (!dateStr) return "—";
        const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
        if (diff < 60) return "Baru saja";
        if (diff < 300) return `${Math.floor(diff / 60)} menit lalu`;
        return new Date(dateStr).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
    };

    return (
        <div className="p-4 md:p-8 space-y-6 max-w-full">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-2">
                    <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-200 to-zinc-500">
                        Pengguna Online
                    </h1>
                    <p className="text-zinc-400 text-sm">User yang aktif dalam 5 menit terakhir (realtime).</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 bg-gradient-to-br from-zinc-900/80 to-[#121212] border border-zinc-800/80 rounded-2xl px-5 py-3 shadow-2xl">
                        <div className="p-2 bg-green-500/10 border border-green-500/20 rounded-xl">
                            <Wifi size={18} className="text-green-400" />
                        </div>
                        <div>
                            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Online Sekarang</p>
                            <p className="text-xl font-black text-white">{total}</p>
                        </div>
                    </div>
                    <button
                        onClick={fetchOnlineUsers}
                        className="p-2.5 rounded-lg bg-zinc-800/50 border border-zinc-700/50 text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors"
                        title="Refresh"
                    >
                        <RefreshCw size={18} />
                    </button>
                    <label className="flex items-center gap-2 text-sm text-zinc-400 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={e => setAutoRefresh(e.target.checked)}
                            className="rounded border-zinc-600 bg-zinc-800 text-green-500 focus:ring-green-500"
                        />
                        Auto-refresh 30s
                    </label>
                </div>
            </div>

            <div className="rounded-2xl border border-zinc-800/60 bg-[#121212]/80 backdrop-blur-sm overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                        <thead className="bg-[#1A1A1A] border-b border-zinc-800 text-xs uppercase text-zinc-500">
                            <tr>
                                <th className="px-4 py-4 font-semibold">Status</th>
                                <th className="px-4 py-4 font-semibold">Pengguna</th>
                                <th className="px-4 py-4 font-semibold">Tipe</th>
                                <th className="px-4 py-4 font-semibold">VIP</th>
                                <th className="px-4 py-4 font-semibold">Terakhir Aktif</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <tr key={i}>
                                        <td className="px-4 py-4"><Skeleton className="h-3 w-3 rounded-full bg-zinc-700" /></td>
                                        <td className="px-4 py-4"><Skeleton className="h-10 w-48 bg-zinc-700" /></td>
                                        <td className="px-4 py-4"><Skeleton className="h-6 w-16 bg-zinc-700" /></td>
                                        <td className="px-4 py-4"><Skeleton className="h-6 w-12 bg-zinc-700" /></td>
                                        <td className="px-4 py-4"><Skeleton className="h-4 w-24 bg-zinc-700" /></td>
                                    </tr>
                                ))
                            ) : users.length > 0 ? (
                                users.map(user => (
                                    <tr key={user.id} className="hover:bg-zinc-800/50 transition-colors">
                                        <td className="px-4 py-4">
                                            <span className="relative flex h-3 w-3">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                                                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500" />
                                            </span>
                                        </td>
                                        <td className="px-4 py-4">
                                            <Link href={`/users/${user.id}`} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                                                <div className="h-9 w-9 rounded-full bg-cyan-600/20 flex items-center justify-center text-cyan-400 font-bold text-xs uppercase flex-shrink-0">
                                                    {user.name?.substring(0, 2) || "??"}
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="font-semibold text-white truncate">{user.name}</p>
                                                    <p className="text-zinc-500 text-xs truncate">{user.email}</p>
                                                </div>
                                            </Link>
                                        </td>
                                        <td className="px-4 py-4">
                                            {user.isGuest ? (
                                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20 w-fit">
                                                    <UserX size={11} /> Tamu
                                                </span>
                                            ) : user.provider === "google" ? (
                                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 w-fit">
                                                    <Chrome size={11} /> Google
                                                </span>
                                            ) : (
                                                <span className="text-xs text-emerald-400">Email</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-4">
                                            {user.vipStatus ? (
                                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 w-fit">
                                                    <Crown size={11} /> VIP
                                                </span>
                                            ) : (
                                                <span className="text-zinc-600 text-xs">—</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-4">
                                            <span className="flex items-center gap-1.5 text-zinc-400 text-xs">
                                                <Clock size={12} className="text-zinc-500" />
                                                {formatLastSeen(user.lastSeen)}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-zinc-500">
                                        <Wifi className="mx-auto mb-2 text-zinc-600" size={32} />
                                        <p>Tidak ada pengguna online saat ini.</p>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
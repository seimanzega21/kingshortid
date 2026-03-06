"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ChevronLeft, User, Mail, Shield, Coins, Eye, Heart, BookMarked,
    MessageSquare, Clock, Calendar, Crown, Ban, Trash2, Loader2,
    Plus, Flame, Wifi
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

interface UserDetail {
    id: string;
    name: string;
    email: string;
    avatar: string | null;
    provider: string;
    role: string;
    coins: number;
    vipStatus: boolean;
    vipExpiry: string | null;
    isGuest: boolean;
    checkInStreak: number;
    totalWatchTime: number;
    bio: string | null;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
    _count: {
        watchHistory: number;
        watchlist: number;
        favorites: number;
        coinTransactions: number;
        comments: number;
    };
    recentHistory: Array<{
        dramaId: string;
        episodeNumber: number;
        progress: number;
        watchedAt: string;
        drama: { title: string; cover: string };
    }>;
}

export default function UserDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const [user, setUser] = useState<UserDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [addCoinsAmount, setAddCoinsAmount] = useState("");
    const [showCoinInput, setShowCoinInput] = useState(false);

    useEffect(() => {
        if (id) fetchUser();
    }, [id]);

    const fetchUser = async () => {
        try {
            const res = await fetch(`/api/users/${id}`);
            if (!res.ok) throw new Error();
            setUser(await res.json());
        } catch {
            toast.error("Gagal memuat data user");
        } finally {
            setLoading(false);
        }
    };

    const handleToggleBan = async () => {
        if (!user) return;
        const action = user.isActive ? "ban" : "unban";
        if (!confirm(`${action === "ban" ? "Ban" : "Unban"} user ini?`)) return;
        setActionLoading(true);
        try {
            const res = await fetch(`/api/users/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ isActive: !user.isActive }),
            });
            if (res.ok) {
                toast.success(`User berhasil di-${action}`);
                fetchUser();
            }
        } catch {
            toast.error("Gagal mengubah status user");
        } finally {
            setActionLoading(false);
        }
    };

    const handleAddCoins = async () => {
        const amount = parseInt(addCoinsAmount);
        if (!amount || amount <= 0) {
            toast.error("Masukkan jumlah koin yang valid");
            return;
        }
        setActionLoading(true);
        try {
            const res = await fetch(`/api/users/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ coins: amount }),
            });
            if (res.ok) {
                toast.success(`${amount} koin ditambahkan`);
                setAddCoinsAmount("");
                setShowCoinInput(false);
                fetchUser();
            }
        } catch {
            toast.error("Gagal menambah koin");
        } finally {
            setActionLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm("HAPUS PERMANEN user ini? Tindakan ini tidak bisa dibatalkan!")) return;
        setActionLoading(true);
        try {
            const res = await fetch(`/api/users/${id}`, { method: "DELETE" });
            if (res.ok) {
                toast.success("User dihapus");
                router.push("/users");
            } else {
                const data = await res.json();
                toast.error(data.message || "Gagal hapus user");
            }
        } catch {
            toast.error("Gagal hapus user");
        } finally {
            setActionLoading(false);
        }
    };

    const formatWatchTime = (seconds: number) => {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        if (hrs > 0) return `${hrs}j ${mins}m`;
        return `${mins}m`;
    };

    if (loading) return (
        <div className="p-8 space-y-6">
            <Skeleton className="h-8 w-32 bg-zinc-800" />
            <Skeleton className="h-48 w-full rounded-xl bg-zinc-800" />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl bg-zinc-800" />)}
            </div>
        </div>
    );

    if (!user) return (
        <div className="p-8 flex flex-col items-center justify-center text-center gap-4">
            <User size={48} className="text-zinc-600" />
            <p className="text-zinc-400">User not found</p>
            <button onClick={() => router.back()} className="text-cyan-500 hover:text-cyan-400">← Kembali</button>
        </div>
    );

    return (
        <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto">
            {/* Back */}
            <button onClick={() => router.push("/users")} className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                <ChevronLeft size={20} />
                <span className="text-sm font-medium">Kembali ke Users</span>
            </button>

            {/* Header Card */}
            <div className="rounded-xl border border-zinc-800 bg-[#111] p-6">
                <div className="flex items-start gap-5">
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                        {user.avatar ? (
                            <img src={user.avatar} alt={user.name} className="w-20 h-20 rounded-full object-cover border-2 border-zinc-700" referrerPolicy="no-referrer" />
                        ) : (
                            <div className="w-20 h-20 rounded-full bg-cyan-600/20 flex items-center justify-center text-cyan-400 font-bold text-2xl uppercase border-2 border-zinc-700">
                                {user.name?.substring(0, 2) || "??"}
                            </div>
                        )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 flex-wrap">
                            <h1 className="text-2xl font-bold text-white">{user.name}</h1>
                            {/* Role badge */}
                            <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${user.role === "admin"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                }`}>
                                {user.role}
                            </span>
                            {/* Status */}
                            <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${user.isActive
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-red-500/10 text-red-400 border-red-500/20"
                                }`}>
                                {user.isActive ? "Active" : "Banned"}
                            </span>
                            {/* Guest */}
                            {user.isGuest && (
                                <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">Guest</span>
                            )}
                            {/* VIP */}
                            {user.vipStatus && (
                                <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                                    <Crown size={12} /> VIP
                                </span>
                            )}
                        </div>

                        <div className="flex items-center gap-4 mt-2 text-sm text-zinc-400 flex-wrap">
                            <span className="flex items-center gap-1.5">
                                <Mail size={14} className="text-zinc-500" /> {user.email}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Shield size={14} className="text-zinc-500" /> {user.provider}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Calendar size={14} className="text-zinc-500" /> {new Date(user.createdAt).toLocaleDateString("id-ID", { year: "numeric", month: "long", day: "numeric" })}
                            </span>
                        </div>

                        {user.bio && <p className="text-sm text-zinc-400 mt-2 italic">&ldquo;{user.bio}&rdquo;</p>}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 flex-shrink-0">
                        <button
                            onClick={handleToggleBan}
                            disabled={actionLoading}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${user.isActive
                                ? "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20"
                                : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20"
                                }`}
                        >
                            {actionLoading ? <Loader2 className="animate-spin" size={14} /> : <Ban size={14} />}
                            {user.isActive ? "Ban User" : "Unban User"}
                        </button>
                        <button
                            onClick={() => setShowCoinInput(!showCoinInput)}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors"
                        >
                            <Plus size={14} /> Tambah Koin
                        </button>
                        <button
                            onClick={handleDelete}
                            disabled={actionLoading || user.role === "admin"}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-zinc-800 text-zinc-400 border border-zinc-700 hover:bg-zinc-700 hover:text-red-400 transition-colors disabled:opacity-40"
                        >
                            <Trash2 size={14} /> Hapus Permanen
                        </button>
                    </div>
                </div>

                {/* Add Coins Input */}
                {showCoinInput && (
                    <div className="mt-4 flex items-center gap-3 p-3 bg-zinc-900 rounded-lg border border-zinc-800">
                        <Coins size={16} className="text-amber-400" />
                        <input
                            type="number"
                            placeholder="Jumlah koin..."
                            className="flex-1 bg-transparent text-white text-sm focus:outline-none"
                            value={addCoinsAmount}
                            onChange={e => setAddCoinsAmount(e.target.value)}
                        />
                        <button
                            onClick={handleAddCoins}
                            disabled={actionLoading}
                            className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                        >
                            {actionLoading ? <Loader2 className="animate-spin" size={14} /> : "Tambah"}
                        </button>
                    </div>
                )}
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <MiniStat icon={Coins} label="Koin" value={user.coins.toLocaleString()} color="amber" />
                <MiniStat icon={Eye} label="Watch History" value={user._count.watchHistory.toString()} color="cyan" />
                <MiniStat icon={BookMarked} label="Watchlist" value={user._count.watchlist.toString()} color="blue" />
                <MiniStat icon={Heart} label="Favorit" value={user._count.favorites.toString()} color="red" />
                <MiniStat icon={Flame} label="Check-In Streak" value={`${user.checkInStreak} hari`} color="orange" />
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                <MiniStat icon={MessageSquare} label="Komentar" value={user._count.comments.toString()} color="emerald" />
                <MiniStat icon={Clock} label="Total Watch Time" value={formatWatchTime(user.totalWatchTime)} color="indigo" />
                <MiniStat icon={Wifi} label="Transaksi Koin" value={user._count.coinTransactions.toString()} color="zinc" />
            </div>

            {/* Recent Watch History */}
            <div className="rounded-xl border border-zinc-800 bg-[#111]">
                <div className="p-5 border-b border-zinc-800">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Eye size={20} className="text-cyan-500" />
                        Riwayat Tonton Terakhir
                    </h3>
                </div>

                <div className="divide-y divide-zinc-800">
                    {(user.recentHistory?.length ?? 0) > 0 ? (
                        user.recentHistory.map((h, i) => (
                            <div key={i} className="flex items-center gap-4 p-4 hover:bg-zinc-800/30 transition-colors">
                                <div className="h-12 w-9 bg-zinc-800 rounded overflow-hidden flex-shrink-0">
                                    {h.drama.cover ? (
                                        <img src={h.drama.cover} alt={h.drama.title} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-zinc-600 text-[10px]">N/A</div>
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-white truncate">{h.drama.title}</p>
                                    <p className="text-xs text-zinc-500">Episode {h.episodeNumber}</p>
                                </div>
                                <div className="text-right flex-shrink-0">
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                            <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${h.progress}%` }} />
                                        </div>
                                        <span className="text-[10px] text-zinc-500 w-7">{h.progress}%</span>
                                    </div>
                                    <p className="text-[10px] text-zinc-600 mt-0.5">
                                        {new Date(h.watchedAt).toLocaleDateString("id-ID")}
                                    </p>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="p-8 text-center text-zinc-500">
                            <Eye className="mx-auto mb-2 text-zinc-600" size={32} />
                            <p>Belum ada riwayat tonton.</p>
                        </div>
                    )}
                </div>
            </div>

            <p className="text-xs text-zinc-600 text-center py-2">
                User ID: <code className="text-zinc-500">{user.id}</code>
            </p>
        </div>
    );
}

function MiniStat({ icon: Icon, label, value, color }: { icon: any; label: string; value: string; color: string }) {
    const colors: Record<string, { bg: string; text: string }> = {
        amber: { bg: "bg-amber-500/10", text: "text-amber-400" },
        cyan: { bg: "bg-cyan-500/10", text: "text-cyan-400" },
        blue: { bg: "bg-blue-500/10", text: "text-blue-400" },
        red: { bg: "bg-red-500/10", text: "text-red-400" },
        orange: { bg: "bg-orange-500/10", text: "text-orange-400" },
        emerald: { bg: "bg-emerald-500/10", text: "text-emerald-400" },
        indigo: { bg: "bg-indigo-500/10", text: "text-indigo-400" },
        zinc: { bg: "bg-zinc-500/10", text: "text-zinc-400" },
    };
    const c = colors[color] || colors.zinc;
    return (
        <div className="rounded-xl border border-zinc-800 bg-[#111] p-4 hover:border-zinc-700 transition-colors">
            <div className={`p-1.5 rounded-lg ${c.bg} ${c.text} w-fit`}>
                <Icon size={16} />
            </div>
            <p className={`text-lg font-bold ${c.text} mt-2`}>{value}</p>
            <p className="text-[11px] text-zinc-500 mt-0.5">{label}</p>
        </div>
    );
}

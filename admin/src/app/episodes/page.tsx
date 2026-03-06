"use client";

import { useState, useEffect } from "react";
import {
    Search,
    Play,
    Lock,
    Unlock,
    Eye,
    MoreVertical,
    Clock,
    Plus,
    Edit,
    Trash2,
    ExternalLink,
    Loader2
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

interface Episode {
    id: string;
    episodeNumber: number;
    title: string;
    thumbnail: string | null;
    videoUrl: string | null;
    duration: number;
    isVip: boolean;
    coinPrice: number;
    views: number;
    createdAt: string;
    drama: {
        id: string;
        title: string;
        cover: string;
    };
}

interface Drama {
    id: string;
    title: string;
}

export default function EpisodesPage() {
    const [episodes, setEpisodes] = useState<Episode[]>([]);
    const [dramas, setDramas] = useState<Drama[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [selectedDrama, setSelectedDrama] = useState("");
    const [selectedType, setSelectedType] = useState("");

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        loadEpisodes();
    }, [selectedDrama, selectedType, search]);

    const loadData = async () => {
        try {
            // Load dramas for filter dropdown
            const dramasRes = await fetch("/api/dramas?limit=100");
            const dramasData = await dramasRes.json();
            setDramas(dramasData.dramas || []);

            await loadEpisodes();
        } catch (error) {
            console.error("Failed to load data:", error);
        }
    };

    const loadEpisodes = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (selectedDrama) params.append("dramaId", selectedDrama);
            if (selectedType === "free") params.append("isVip", "false");
            if (selectedType === "vip") params.append("isVip", "true");
            if (search) params.append("q", search);

            const res = await fetch(`/api/episodes?${params}`);
            const data = await res.json();
            setEpisodes(data.episodes || []);
        } catch (error) {
            console.error("Failed to load episodes:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (episodeId: string) => {
        if (!confirm("Hapus episode ini?")) return;

        try {
            const res = await fetch(`/api/episodes/${episodeId}`, { method: "DELETE" });
            if (res.ok) {
                toast.success("Episode dihapus");
                loadEpisodes();
            } else {
                toast.error("Gagal menghapus episode");
            }
        } catch {
            toast.error("Gagal menghapus episode");
        }
    };

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 0) return `${diffDays}d ago`;
        if (diffHours > 0) return `${diffHours}h ago`;
        return "Just now";
    };

    const formatViews = (views: number) => {
        if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
        if (views >= 1000) return `${(views / 1000).toFixed(0)}k`;
        return views.toString();
    };

    return (
        <div className="p-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Manajemen Episode</h1>
                    <p className="text-zinc-400 mt-1">Daftar semua episode video yang telah diupload.</p>
                </div>
                <Link href="/episodes/new" className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors">
                    <Plus size={18} />
                    <span>Upload Episode</span>
                </Link>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4 justify-between bg-[#121212] p-4 rounded-xl border border-zinc-800">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                    <input
                        type="text"
                        placeholder="Cari episode atau judul drama..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-black/50 border border-zinc-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
                    />
                </div>
                <div className="flex gap-2">
                    <select
                        value={selectedDrama}
                        onChange={(e) => setSelectedDrama(e.target.value)}
                        className="bg-black/50 border border-zinc-700 text-zinc-400 text-sm rounded-lg px-4 py-2 outline-none focus:border-purple-500"
                    >
                        <option value="">Filter Drama: Semua</option>
                        {dramas.map(d => (
                            <option key={d.id} value={d.id}>{d.title}</option>
                        ))}
                    </select>
                    <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="bg-black/50 border border-zinc-700 text-zinc-400 text-sm rounded-lg px-4 py-2 outline-none focus:border-purple-500"
                    >
                        <option value="">Tipe: Semua</option>
                        <option value="free">Free</option>
                        <option value="vip">VIP / Coin</option>
                    </select>
                </div>
            </div>

            {/* Episodes Grid */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="animate-spin text-purple-500" size={40} />
                </div>
            ) : episodes.length === 0 ? (
                <div className="text-center py-20">
                    <p className="text-zinc-500 text-lg">Tidak ada episode ditemukan</p>
                    <Link href="/episodes/new" className="text-purple-500 hover:underline mt-2 inline-block">
                        Upload episode pertama →
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {episodes.map((episode) => (
                        <div key={episode.id} className="group rounded-xl border border-zinc-800 bg-[#121212] overflow-hidden hover:border-purple-500/50 transition-all">
                            {/* Thumbnail */}
                            <div className="relative aspect-video bg-zinc-900">
                                {episode.thumbnail ? (
                                    <img src={episode.thumbnail} alt={episode.title} className="w-full h-full object-cover" />
                                ) : episode.drama?.cover ? (
                                    <img src={episode.drama.cover} alt={episode.title} className="w-full h-full object-cover opacity-50" />
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <Play className="text-zinc-600 fill-zinc-600 group-hover:text-purple-500 group-hover:fill-purple-500 transition-colors" size={40} />
                                    </div>
                                )}

                                {/* Play overlay */}
                                {episode.videoUrl && (
                                    <a
                                        href={episode.videoUrl}
                                        target="_blank"
                                        className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Play className="text-white fill-white" size={48} />
                                    </a>
                                )}

                                {/* Badges */}
                                <div className="absolute top-2 left-2 flex gap-1">
                                    <span className="bg-black/60 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-0.5 rounded">
                                        EPS {episode.episodeNumber}
                                    </span>
                                </div>
                                <div className="absolute top-2 right-2">
                                    {episode.isVip ? (
                                        <span className="bg-yellow-500 text-black text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                            <Lock size={10} /> VIP
                                        </span>
                                    ) : (
                                        <span className="bg-green-500 text-black text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1">
                                            <Unlock size={10} /> FREE
                                        </span>
                                    )}
                                </div>
                                <div className="absolute bottom-2 right-2 bg-black/80 text-white text-[10px] px-1.5 py-0.5 rounded">
                                    {formatDuration(episode.duration)}
                                </div>
                            </div>

                            {/* Details */}
                            <div className="p-4">
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-white line-clamp-1">{episode.title}</h4>
                                        <Link href={`/dramas/${episode.drama?.id}`} className="text-xs text-purple-400 hover:underline line-clamp-1">
                                            {episode.drama?.title}
                                        </Link>
                                    </div>
                                    <div className="relative group/menu">
                                        <button className="text-zinc-500 hover:text-white p-1">
                                            <MoreVertical size={16} />
                                        </button>
                                        <div className="absolute right-0 top-full mt-1 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible transition-all z-10 min-w-[140px]">
                                            <Link
                                                href={`/episodes/${episode.id}/edit`}
                                                className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
                                            >
                                                <Edit size={14} /> Edit
                                            </Link>
                                            {episode.videoUrl && (
                                                <a
                                                    href={episode.videoUrl}
                                                    target="_blank"
                                                    className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
                                                >
                                                    <ExternalLink size={14} /> Preview
                                                </a>
                                            )}
                                            <button
                                                onClick={() => handleDelete(episode.id)}
                                                className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-zinc-800 hover:text-red-300 w-full"
                                            >
                                                <Trash2 size={14} /> Hapus
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4 mt-4 text-xs text-zinc-500 border-t border-zinc-800 pt-3">
                                    <div className="flex items-center gap-1">
                                        <Eye size={14} /> {formatViews(episode.views)}
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Clock size={14} /> {formatTimeAgo(episode.createdAt)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

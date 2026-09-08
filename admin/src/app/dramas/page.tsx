"use client";

import { useState, useEffect } from "react";
import { Search, Plus, Film, CheckCircle, Eye, MoreVertical, Smartphone, Trash2, Loader2, AlertTriangle, Bell, LayoutGrid, List, Lock } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "next/navigation";

interface Drama {
    id: string;
    title: string;
    description: string;
    status: string;
    totalEpisodes: number;
    views: number;
    createdAt: string;
    cover: string;
    genres: string[];
    isActive: boolean;
    isVip: boolean;
}

// Gradient colors for fallback covers
const coverColors = [
    'from-cyan-600 to-blue-700',
    'from-emerald-600 to-teal-700',
    'from-amber-600 to-orange-700',
    'from-rose-600 to-pink-700',
    'from-violet-600 to-purple-700',
    'from-sky-600 to-indigo-700',
];

function CoverImage({ cover, title }: { cover: string; title: string }) {
    const [failed, setFailed] = useState(false);
    const initial = title?.charAt(0)?.toUpperCase() || '?';
    const colorIdx = title ? title.charCodeAt(0) % coverColors.length : 0;

    // Support both absolute URLs (https://...) and relative URLs (/api/uploads/...)
    const isValidCover = cover && (cover.startsWith('http') || cover.startsWith('/'));
    // Add cache-bust to force CDN to serve fresh WebP (not old cached HEIC)
    const imgSrc = isValidCover
        ? (cover.includes('?') ? `${cover}&v=2` : `${cover}?v=2`)
        : cover;

    if (!isValidCover || failed) {
        return (
            <div className={`w-[48px] h-[72px] rounded-lg overflow-hidden flex-shrink-0 ring-1 ring-white/5 bg-gradient-to-br ${coverColors[colorIdx]} flex items-center justify-center`}>
                <span className="text-white/90 text-lg font-bold">{initial}</span>
            </div>
        );
    }

    return (
        <div className="w-[48px] h-[72px] rounded-lg overflow-hidden bg-zinc-800 flex-shrink-0 ring-1 ring-white/5 group-hover:ring-cyan-500/20 transition-all">
            <img src={imgSrc} alt="" className="w-full h-full object-cover" loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} />
        </div>
    );
}

// Large cover for grid view (portrait 3:4 ratio)
function CoverImageLarge({ cover, title }: { cover: string; title: string }) {
    const [failed, setFailed] = useState(false);
    const initial = title?.charAt(0)?.toUpperCase() || '?';
    const colorIdx = title ? title.charCodeAt(0) % coverColors.length : 0;

    const isValidCover = cover && (cover.startsWith('http') || cover.startsWith('/'));
    const imgSrc = isValidCover
        ? (cover.includes('?') ? `${cover}&v=2` : `${cover}?v=2`)
        : cover;

    if (!isValidCover || failed) {
        return (
            <div className={`w-full aspect-[3/4] rounded-xl overflow-hidden bg-gradient-to-br ${coverColors[colorIdx]} flex items-center justify-center`}>
                <span className="text-white/90 text-4xl font-bold">{initial}</span>
            </div>
        );
    }

    return (
        <div className="w-full aspect-[3/4] rounded-xl overflow-hidden bg-zinc-800">
            <img src={imgSrc} alt={title} className="w-full h-full object-cover" loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} />
        </div>
    );
}

export default function DramaManagement() {
    const [dramas, setDramas] = useState<Drama[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [publishFilter, setPublishFilter] = useState<"all" | "tayang" | "pending" | "anime" | "vip">("all");
    const [statusFilter, setStatusFilter] = useState<"all" | "completed" | "ongoing">("all");
    const [sortOrder, setSortOrder] = useState<"newest" | "az" | "za">("newest");
    const [viewMode, setViewMode] = useState<"list" | "grid">("list");

    // Initialize from sessionStorage on mount
    useEffect(() => {
        if (typeof window !== "undefined") {
            const savedSearch = sessionStorage.getItem("drama_searchTerm");
            const savedTab = sessionStorage.getItem("drama_publishFilter") as any;
            const savedStatus = sessionStorage.getItem("drama_statusFilter") as any;
            const savedView = sessionStorage.getItem("drama_viewMode") as any;
            if (savedSearch) setSearchTerm(savedSearch);
            if (savedTab) setPublishFilter(savedTab);
            if (savedStatus) setStatusFilter(savedStatus);
            if (savedView) setViewMode(savedView);
        }
    }, []);

    // Save to sessionStorage on change
    useEffect(() => {
        sessionStorage.setItem("drama_searchTerm", searchTerm);
        sessionStorage.setItem("drama_publishFilter", publishFilter);
        sessionStorage.setItem("drama_statusFilter", statusFilter);
        sessionStorage.setItem("drama_viewMode", viewMode);
    }, [searchTerm, publishFilter, statusFilter, viewMode]);
    const [publishingId, setPublishingId] = useState<string | null>(null);
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
    const [completing, setCompleting] = useState(false);
    
    // Delete Modal State
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [targetDeleteId, setTargetDeleteId] = useState<string | null>(null);
    const [deleteFromR2, setDeleteFromR2] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    
    const router = useRouter();

    useEffect(() => { fetchDramas(); }, []);



    const fetchDramas = async () => {
        try {
            const res = await fetch(`/api/dramas?includeInactive=true&limit=9999&_t=${Date.now()}`, {
                cache: 'no-store',
                headers: { 'Cache-Control': 'no-cache' }
            });
            const data = await res.json();
            if (Array.isArray(data)) setDramas(data);
            else if (data.dramas) setDramas(data.dramas);
        } catch { toast.error("Gagal memuat daftar drama"); }
        finally { setIsLoading(false); }
    };

    const openDeleteModal = (id: string) => {
        setTargetDeleteId(id);
        setDeleteFromR2(false); // default unchecked
        setDeleteModalOpen(true);
        setMenuOpenId(null);
    };

    const confirmDelete = async () => {
        if (!targetDeleteId) return;
        const deletedId = targetDeleteId;
        setIsDeleting(true);
        try {
            const res = await fetch(`/api/dramas/${deletedId}?deleteFromR2=${deleteFromR2}`, { method: "DELETE" });
            if (res.ok) {
                toast.success(deleteFromR2 ? "Drama & file R2 dihapus permanen" : "Drama berhasil dihapus");
                // Optimistic UI update: langsung buang dari layar seketika tanpa perlu F5
                setDramas(prev => prev.filter(d => d.id !== deletedId));
                fetchDramas();
            } else {
                toast.error("Gagal menghapus drama");
            }
        } catch {
            toast.error("Terjadi kesalahan jaringan");
        } finally {
            setIsDeleting(false);
            setDeleteModalOpen(false);
            setTargetDeleteId(null);
        }
    };

    const togglePublish = async (id: string, currentActive: boolean) => {
        setPublishingId(id);
        setMenuOpenId(null);
        try {
            const res = await fetch(`/api/dramas/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ isActive: !currentActive }),
            });
            if (res.ok) {
                toast.success(currentActive ? "Drama dipending dari mobile" : "Drama ditayangkan ke mobile");
                fetchDramas();
            }
        } catch { toast.error("Terjadi kesalahan"); }
        finally { setPublishingId(null); }
    };

    const sendPushNotification = async (id: string, title?: string) => {
        setPublishingId(id);
        setMenuOpenId(null);
        try {
            const dramaTitle = title || "Drama Baru";
            const res = await fetch("/api/notifications/broadcast", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: "Drama Baru Tersedia 🎬",
                    body: `"${dramaTitle}" sudah bisa ditonton sekarang!`,
                    type: "new_drama",
                    dramaId: id,
                    categoryId: "DRAMA_ACTION",
                    imageUrl: dramas.find(d => d.id === id)?.cover || undefined,
                }),
            });
            if (res.ok) {
                toast.success(`Notifikasi push (baru rilis)  terkirim ke semua user! 🔔`);
            } else {
                toast.error("Gagal mengirim notifikasi push");
            }
        } catch { toast.error("Terjadi kesalahan sistem"); }
        finally { setPublishingId(null); }
    };

    const totalAll = dramas.length;
    const healthyCount = dramas.filter(d =>
        d.isActive !== false && d.cover && d.cover.length > 5 && d.description && d.description.length > 10 && d.totalEpisodes > 0
    ).length;
    const pendingCount = totalAll - healthyCount;

    const isAnime = (d: Drama) => {
        const ANIME_KW = ['anime', 'animasi', 'kartun', 'donghua'];
        return ANIME_KW.some(kw => 
            (d.title || '').toLowerCase().includes(kw) || 
            (d.genres || []).some(g => g.toLowerCase().includes(kw))
        );
    };
    const animeCount = dramas.filter(isAnime).length;
    const vipCount = dramas.filter(d => d.isVip).length;

    // Apply all filters
    let filteredDramas = dramas.filter(d => {
        // Search
        if (searchTerm && !d.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;

        // Publish filter (Tabs)
        if (publishFilter === "tayang" && d.isActive === false) return false;
        if (publishFilter === "pending" && d.isActive !== false) return false;
        if (publishFilter === "anime" && !isAnime(d)) return false;
        if (publishFilter === "vip" && !d.isVip) return false;

        // Status filter
        if (statusFilter !== "all" && d.status !== statusFilter) return false;

        return true;
    });

    // Sort
    if (sortOrder === "az") {
        filteredDramas = [...filteredDramas].sort((a, b) => a.title.localeCompare(b.title, 'id'));
    } else if (sortOrder === "za") {
        filteredDramas = [...filteredDramas].sort((a, b) => b.title.localeCompare(a.title, 'id'));
    }
    // "newest" uses default API order (createdAt desc)

    const selectClass = "bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-cyan-500/50 cursor-pointer appearance-none";

    return (
        <div>
            {/* ============ STICKY TOP ============ */}
            <div className="sticky top-0 z-30 bg-[#09090b]">
                {/* Header */}
                <div className="px-8 pt-6 pb-4">
                    <div className="flex items-center justify-between mb-5">
                        <div>
                            <h1 className="text-2xl font-bold text-white">Manajemen Drama</h1>
                            <p className="text-zinc-500 text-sm mt-0.5">Kelola katalog, publikasi ke mobile, dan atur konten drama.</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={async () => {
                                    const ongoing = dramas.filter(d => d.status === 'ongoing').length;
                                    if (ongoing === 0) { toast.info('Semua drama sudah komplit'); return; }
                                    if (!confirm(`Tandai ${ongoing} drama ongoing sebagai komplit?`)) return;
                                    setCompleting(true);
                                    try {
                                        const res = await fetch('/api/dramas/bulk-complete', { method: 'POST' });
                                        const data = await res.json();
                                        toast.success(`${data.count} drama ditandai komplit`);
                                        fetchDramas();
                                    } catch { toast.error('Gagal menandai komplit'); }
                                    setCompleting(false);
                                }}
                                disabled={completing}
                                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-lg font-semibold text-sm shadow-lg shadow-emerald-500/10 disabled:opacity-50 transition-colors"
                            >
                                <CheckCircle size={16} className={completing ? 'animate-spin' : ''} />
                                {completing ? 'Memproses...' : 'Komplit Semua'}
                            </button>
                            <Link href="/dramas/new" className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-5 py-2.5 rounded-lg font-semibold text-sm shadow-lg shadow-cyan-500/10">
                                <Plus size={16} /> Tambah Drama
                            </Link>
                        </div>
                    </div>

                    {/* Navigation Tabs for Separation */}
                    <div className="flex border-b border-zinc-800/80 mb-5">
                        <button 
                            onClick={() => setPublishFilter("all")} 
                            className={`px-6 py-3 text-sm font-semibold border-b-2 transition-colors flex gap-2 items-center ${publishFilter === "all" ? "border-cyan-500 text-cyan-400" : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700"}`}
                        >
                            Total Semua Drama <span className={`px-2 py-0.5 rounded-full text-xs ${publishFilter === "all" ? "bg-cyan-500/20 text-cyan-300" : "bg-zinc-800 text-zinc-400"}`}>{totalAll}</span>
                        </button>
                        <button 
                            onClick={() => setPublishFilter("tayang")} 
                            className={`px-6 py-3 text-sm font-semibold border-b-2 transition-colors flex gap-2 items-center ${publishFilter === "tayang" ? "border-emerald-500 text-emerald-400" : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700"}`}
                        >
                            Sedang Tayang <span className={`px-2 py-0.5 rounded-full text-xs ${publishFilter === "tayang" ? "bg-emerald-500/20 text-emerald-300" : "bg-zinc-800 text-zinc-400"}`}>{healthyCount}</span>
                        </button>
                        <button 
                            onClick={() => setPublishFilter("pending")} 
                            className={`px-6 py-3 text-sm font-semibold border-b-2 transition-colors flex gap-2 items-center ${publishFilter === "pending" ? "border-amber-500 text-amber-400" : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700"}`}
                        >
                            Pending (Belum Tayang) <span className={`px-2 py-0.5 rounded-full text-xs ${publishFilter === "pending" ? "bg-amber-500/20 text-amber-300" : "bg-zinc-800 text-zinc-400"}`}>{pendingCount}</span>
                        </button>
                        <button 
                            onClick={() => setPublishFilter("anime")} 
                            className={`px-6 py-3 text-sm font-semibold border-b-2 transition-colors flex gap-2 items-center ${publishFilter === "anime" ? "border-purple-500 text-purple-400" : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700"}`}
                        >
                            Khusus Anime <span className={`px-2 py-0.5 rounded-full text-xs ${publishFilter === "anime" ? "bg-purple-500/20 text-purple-300" : "bg-zinc-800 text-zinc-400"}`}>{animeCount}</span>
                        </button>
                        <button 
                            onClick={() => setPublishFilter("vip")} 
                            className={`px-6 py-3 text-sm font-semibold border-b-2 transition-colors flex gap-2 items-center ${publishFilter === "vip" ? "border-yellow-500 text-yellow-400" : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700"}`}
                        >
                            Khusus VIP <span className={`px-2 py-0.5 rounded-full text-xs ${publishFilter === "vip" ? "bg-yellow-500/20 text-yellow-300" : "bg-zinc-800 text-zinc-400"}`}>{vipCount}</span>
                        </button>
                    </div>

                    {/* Search + Filters Row */}
                    <div className="flex items-center gap-3 flex-wrap">
                        {/* Search */}
                        <div className="relative flex-1 min-w-[200px] max-w-sm">
                            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
                            <input type="text" placeholder="Cari drama..."
                                className="w-full bg-zinc-900/80 border border-zinc-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500/50"
                                value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                        </div>

                        {/* Filter Status */}
                        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as any)} className={selectClass}>
                            <option value="all">Semua Status</option>
                            <option value="completed">Komplit</option>
                            <option value="ongoing">Ongoing</option>
                        </select>

                        {/* Sort */}
                        <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as any)} className={selectClass}>
                            <option value="newest">Terbaru</option>
                            <option value="az">A → Z</option>
                            <option value="za">Z → A</option>
                        </select>

                        {/* Count */}
                        <span className="text-sm text-zinc-600 ml-auto">{filteredDramas.length} drama</span>

                        {/* View Toggle */}
                        <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1">
                            <button
                                onClick={() => setViewMode('list')}
                                title="Tampilan List"
                                className={`p-1.5 rounded-md transition-colors ${
                                    viewMode === 'list'
                                        ? 'bg-cyan-600 text-white'
                                        : 'text-zinc-500 hover:text-zinc-300'
                                }`}
                            >
                                <List size={16} />
                            </button>
                            <button
                                onClick={() => setViewMode('grid')}
                                title="Tampilan Grid"
                                className={`p-1.5 rounded-md transition-colors ${
                                    viewMode === 'grid'
                                        ? 'bg-cyan-600 text-white'
                                        : 'text-zinc-500 hover:text-zinc-300'
                                }`}
                            >
                                <LayoutGrid size={16} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Table Header — hanya tampil di List View */}
                {viewMode === 'list' && (
                <div className="px-8 py-3 bg-[#0c0c0c] border-y border-zinc-800/70">
                    <div className="grid grid-cols-[36px_56px_1fr_100px_72px_100px_80px_80px_44px] gap-4 items-center">
                        <span className="text-xs font-semibold text-zinc-500 uppercase">No</span>
                        <span></span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase">Drama</span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase">Publikasi</span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase">Episode</span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase">Status</span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase">Tayang</span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase">Tanggal</span>
                        <span className="text-xs font-semibold text-zinc-500 uppercase text-center">Aksi</span>
                    </div>
                </div>
                )}
            </div>

            {/* ============ TABLE BODY ============ */}
            <div className="px-8">
                {isLoading ? (
                    viewMode === 'grid' ? (
                        // Grid skeleton
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7 gap-4 py-6">
                            {Array(12).fill(0).map((_, i) => (
                                <div key={i} className="space-y-2">
                                    <Skeleton className="w-full aspect-[3/4] rounded-xl bg-zinc-800" />
                                    <Skeleton className="h-4 w-3/4 bg-zinc-800" />
                                </div>
                            ))}
                        </div>
                    ) : (
                        // List skeleton
                        Array(10).fill(0).map((_, i) => (
                            <div key={i} className="grid grid-cols-[36px_56px_1fr_100px_72px_100px_80px_80px_44px] gap-4 items-center py-4 border-b border-zinc-800/30">
                                <Skeleton className="h-4 w-5 bg-zinc-800" />
                                <Skeleton className="h-[72px] w-[48px] rounded-lg bg-zinc-800" />
                                <div className="space-y-2"><Skeleton className="h-4 w-44 bg-zinc-800" /><Skeleton className="h-3 w-64 bg-zinc-800" /></div>
                                <Skeleton className="h-6 w-16 bg-zinc-800" />
                                <Skeleton className="h-4 w-8 bg-zinc-800" />
                                <Skeleton className="h-6 w-16 bg-zinc-800" />
                                <Skeleton className="h-4 w-10 bg-zinc-800" />
                                <Skeleton className="h-4 w-14 bg-zinc-800" />
                                <Skeleton className="h-4 w-6 bg-zinc-800" />
                            </div>
                        ))
                    )
                ) : filteredDramas.length > 0 ? (
                    viewMode === 'grid' ? (
                        // ============ GRID VIEW ============
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7 gap-4 py-6">
                            {filteredDramas.map((item) => (
                                <div
                                    key={item.id}
                                    className="group cursor-pointer"
                                    onClick={() => router.push(`/dramas/${item.id}`)}
                                >
                                    {/* Cover dengan hover efek naik */}
                                    <div className="relative rounded-xl overflow-hidden transition-transform duration-200 group-hover:-translate-y-1.5">
                                        <CoverImageLarge cover={item.cover} title={item.title} />
                                        {item.isVip && (
                                            <div className="absolute top-2 right-2 bg-yellow-500 text-black text-[10px] font-bold px-1.5 py-0.5 rounded shadow-lg flex items-center gap-1">
                                                <Lock size={10} /> VIP
                                            </div>
                                        )}
                                    </div>
                                    {/* Judul */}
                                    <p className="mt-2 text-[12px] font-medium text-zinc-300 group-hover:text-cyan-400 transition-colors line-clamp-2 leading-snug">
                                        {item.title}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        // ============ LIST VIEW ============
                        filteredDramas.map((item, idx) => {
                            const isHealthy = item.isActive !== false && item.cover && item.cover.length > 5 && item.description && item.description.length > 10 && item.totalEpisodes > 0;
                            return (
                                <div key={item.id}
                                    className={`grid grid-cols-[36px_56px_1fr_100px_72px_100px_80px_80px_44px] gap-4 items-center py-3 border-b border-zinc-800/30 hover:bg-white/[0.02] transition-colors cursor-pointer group ${!isHealthy ? 'opacity-60' : ''} ${menuOpenId === item.id ? 'relative z-50' : ''}`}
                                    onClick={(e) => {
                                        const target = e.target as HTMLElement;
                                        if (target.closest('[data-menu-area]')) return;
                                        router.push(`/dramas/${item.id}`);
                                    }}>

                                    {/* No */}
                                    <span className="text-sm text-zinc-600 font-mono">{idx + 1}</span>

                                    {/* Cover */}
                                    <CoverImage cover={item.cover} title={item.title} />

                                    {/* Judul + Deskripsi */}
                                    <div className="min-w-0 pr-4">
                                        <div className="flex items-center gap-2">
                                            <p className="text-[13px] font-semibold text-white group-hover:text-cyan-400 transition-colors truncate leading-tight">
                                                {item.title}
                                            </p>
                                            {item.isVip && (
                                                <span className="bg-yellow-500/20 text-yellow-500 text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 whitespace-nowrap flex-shrink-0">
                                                    <Lock size={10} /> VIP
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-[12px] text-zinc-500 mt-1 line-clamp-2 leading-snug">
                                            {item.description || <span className="italic text-zinc-700">Belum ada deskripsi</span>}
                                        </p>
                                        <div className="flex gap-1 mt-1.5">
                                            {item.genres?.slice(0, 3).map(g => (
                                                <span key={g} className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800/80 text-zinc-500">{g}</span>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Publikasi */}
                                    <div>
                                        {item.isActive !== false ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                                Tayang
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                                                Pending
                                            </span>
                                        )}
                                    </div>

                                    {/* Episode */}
                                    <span className="text-sm text-zinc-300 font-medium">{item.totalEpisodes}</span>

                                    {/* Status */}
                                    <span className={`inline-flex px-2.5 py-1 rounded-full text-[11px] font-semibold border w-fit ${item.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                        item.status === 'ongoing' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                            'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                                        }`}>{item.status === 'completed' ? 'Komplit' : item.status === 'ongoing' ? 'Ongoing' : 'Draft'}</span>

                                    {/* Tayang (Views) */}
                                    <div className="flex items-center gap-1.5 text-sm text-zinc-400">
                                        <Eye size={13} className="text-zinc-600" />
                                        {(item.views || 0).toLocaleString()}
                                    </div>

                                    {/* Tanggal */}
                                    <span className="text-[11px] text-zinc-500">{new Date(item.createdAt).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: '2-digit' })}</span>

                                    {/* Menu ⋮ */}
                                    <div className="relative flex justify-center" data-menu-area onClick={e => e.stopPropagation()}>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setMenuOpenId(menuOpenId === item.id ? null : item.id);
                                            }}
                                            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-white transition-colors"
                                        >
                                            {publishingId === item.id ? <Loader2 size={16} className="animate-spin" /> : <MoreVertical size={16} />}
                                        </button>

                                        {menuOpenId === item.id && (
                                            <>
                                                {/* Backdrop to close menu on outside click */}
                                                <div className="fixed inset-0 z-[99]" data-menu-area onClick={(e) => { e.stopPropagation(); setMenuOpenId(null); }} />
                                                <div className="absolute right-0 top-full mt-1 w-56 rounded-xl shadow-2xl shadow-black/80 z-[100] py-1 isolate pointer-events-auto bg-[#2a2a2e] border-2 border-zinc-600" data-menu-area>
                                                    <button
                                                        onMouseDown={(e) => {
                                                            e.stopPropagation();
                                                            e.preventDefault();
                                                            togglePublish(item.id, item.isActive !== false);
                                                        }}
                                                        className="w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-zinc-500/20 transition-colors cursor-pointer"
                                                    >
                                                        <Smartphone size={16} className={item.isActive !== false ? "text-amber-400" : "text-emerald-400"} />
                                                        <span className={item.isActive !== false ? "text-amber-300" : "text-emerald-300"}>
                                                            {item.isActive !== false ? "Pending dari Mobile" : "Tayangkan ke Mobile"}
                                                        </span>
                                                    </button>
                                                    {item.isActive !== false && (
                                                        <button
                                                            onMouseDown={(e) => {
                                                                e.stopPropagation();
                                                                e.preventDefault();
                                                                sendPushNotification(item.id, item.title);
                                                            }}
                                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-blue-500/20 transition-colors cursor-pointer"
                                                        >
                                                            <Bell size={16} className="text-blue-400" />
                                                            <span className="text-blue-300">
                                                                Kirim Notif Baru Tayang
                                                            </span>
                                                        </button>
                                                    )}
                                                    <div className="border-t border-zinc-600 my-0.5" />
                                                    <button
                                                        onMouseDown={(e) => {
                                                            e.stopPropagation();
                                                            e.preventDefault();
                                                            openDeleteModal(item.id);
                                                        }}
                                                        className="w-full flex items-center gap-3 px-4 py-3 text-sm hover:bg-red-500/20 text-red-400 transition-colors cursor-pointer"
                                                    >
                                                        <Trash2 size={16} /> Hapus Drama
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )
                ) : (
                    <div className="py-24 text-center">
                        <Film size={40} className="mx-auto text-zinc-700 mb-3" />
                        <p className="text-zinc-500">Tidak ada drama ditemukan.</p>
                    </div>
                )}
            </div>
            
            {/* Delete Confirmation Modal */}
            {deleteModalOpen && (
                <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <div className="bg-[#18181b] border border-zinc-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                        <div className="p-6">
                            <div className="flex items-center gap-3 text-red-500 mb-4">
                                <AlertTriangle size={24} />
                                <h3 className="text-xl font-bold text-white">Hapus Drama</h3>
                            </div>
                            <p className="text-zinc-400 text-sm mb-6">
                                Anda yakin ingin menghapus drama ini? Tindakan ini akan menghapus data drama dan episodenya dari database.
                            </p>
                            
                            <label className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl cursor-pointer hover:bg-red-500/20 transition-colors">
                                <input 
                                    type="checkbox" 
                                    checked={deleteFromR2}
                                    onChange={(e) => setDeleteFromR2(e.target.checked)}
                                    className="mt-1 w-4 h-4 rounded border-red-500/50 bg-black/50 text-red-500 focus:ring-red-500 focus:ring-offset-0"
                                />
                                <div>
                                    <p className="text-sm font-semibold text-red-400">Hapus juga file dari Server (R2)?</p>
                                    <p className="text-xs text-red-400/80 mt-1 leading-snug">
                                        Mencentang ini akan menghapus permanen semua video episode dan cover dari Cloudflare R2 untuk menghemat penyimpanan.
                                    </p>
                                </div>
                            </label>
                        </div>
                        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-[#121214] border-t border-zinc-800">
                            <button 
                                onClick={() => setDeleteModalOpen(false)}
                                disabled={isDeleting}
                                className="px-4 py-2 text-sm font-medium text-zinc-300 hover:text-white transition-colors"
                            >
                                Batal
                            </button>
                            <button 
                                onClick={confirmDelete}
                                disabled={isDeleting}
                                className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg text-sm font-bold shadow-lg shadow-red-600/20 transition-colors disabled:opacity-50"
                            >
                                {isDeleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                                {isDeleting ? "Menghapus..." : "Hapus Permanen"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

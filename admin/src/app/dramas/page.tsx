"use client";

import { useState, useEffect } from "react";
import { Search, Plus, Film, CheckCircle, Eye, MoreVertical, Smartphone, Trash2, Loader2, AlertTriangle } from "lucide-react";
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

    // Add cache-bust to force CDN to serve fresh WebP (not old cached HEIC)
    const imgSrc = cover && cover.startsWith('http')
        ? (cover.includes('?') ? `${cover}&v=2` : `${cover}?v=2`)
        : cover;

    if (!cover || !cover.startsWith('http') || failed) {
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

export default function DramaManagement() {
    const [dramas, setDramas] = useState<Drama[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [activeFilter, setActiveFilter] = useState<"all" | "active" | "inactive">("all");
    const [publishFilter, setPublishFilter] = useState<"all" | "tayang" | "pending">("all");
    const [statusFilter, setStatusFilter] = useState<"all" | "completed" | "ongoing">("all");
    const [sortOrder, setSortOrder] = useState<"newest" | "az" | "za">("newest");
    const [publishingId, setPublishingId] = useState<string | null>(null);
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
    const [completing, setCompleting] = useState(false);
    const router = useRouter();

    useEffect(() => { fetchDramas(); }, []);



    const fetchDramas = async () => {
        try {
            const res = await fetch("/api/dramas?includeInactive=true&limit=9999");
            const data = await res.json();
            if (Array.isArray(data)) setDramas(data);
            else if (data.dramas) setDramas(data.dramas);
        } catch { toast.error("Gagal memuat daftar drama"); }
        finally { setIsLoading(false); }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Apakah Anda yakin ingin menghapus drama ini?")) return;
        try {
            const res = await fetch(`/api/dramas/${id}`, { method: "DELETE" });
            if (res.ok) { toast.success("Drama berhasil dihapus"); fetchDramas(); }
        } catch { toast.error("Terjadi kesalahan"); }
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

    const totalAll = dramas.length;
    const healthyCount = dramas.filter(d =>
        d.isActive !== false && d.cover && d.cover.length > 5 && d.description && d.description.length > 10 && d.totalEpisodes > 0
    ).length;
    const pendingCount = totalAll - healthyCount;

    // Apply all filters
    let filteredDramas = dramas.filter(d => {
        // Search
        if (searchTerm && !d.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;

        // Stats card filter
        if (activeFilter === "active") {
            const ok = d.isActive !== false && d.cover && d.cover.length > 5 && d.description && d.description.length > 10 && d.totalEpisodes > 0;
            if (!ok) return false;
        }
        if (activeFilter === "inactive") {
            const ok = d.isActive !== false && d.cover && d.cover.length > 5 && d.description && d.description.length > 10 && d.totalEpisodes > 0;
            if (ok) return false;
        }

        // Publish filter
        if (publishFilter === "tayang" && d.isActive === false) return false;
        if (publishFilter === "pending" && d.isActive !== false) return false;

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

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-3 mb-4">
                        <button onClick={() => setActiveFilter("all")}
                            className={`rounded-xl border p-4 text-left transition-all ${activeFilter === "all" ? "border-cyan-500/40 bg-cyan-500/5" : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"}`}>
                            <div className="flex items-center gap-3">
                                <div className={`p-2.5 rounded-xl ${activeFilter === "all" ? "bg-cyan-500/15 text-cyan-400" : "bg-zinc-800 text-zinc-500"}`}><Film size={18} /></div>
                                <div><span className="text-2xl font-bold text-white">{totalAll}</span><p className="text-xs text-zinc-500">Total Drama</p></div>
                            </div>
                        </button>
                        <button onClick={() => setActiveFilter(activeFilter === "active" ? "all" : "active")}
                            className={`rounded-xl border p-4 text-left transition-all ${activeFilter === "active" ? "border-emerald-500/40 bg-emerald-500/5" : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"}`}>
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400"><CheckCircle size={18} /></div>
                                <div><span className="text-2xl font-bold text-white">{healthyCount}</span><p className="text-xs text-zinc-500">Tayang di Mobile</p></div>
                            </div>
                        </button>
                        <button onClick={() => setActiveFilter(activeFilter === "inactive" ? "all" : "inactive")}
                            className={`rounded-xl border p-4 text-left transition-all ${activeFilter === "inactive" ? "border-amber-500/40 bg-amber-500/5" : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"}`}>
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400"><AlertTriangle size={18} /></div>
                                <div><span className="text-2xl font-bold text-white">{pendingCount}</span><p className="text-xs text-zinc-500">Belum Publikasi</p></div>
                            </div>
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

                        {/* Filter Publikasi */}
                        <select value={publishFilter} onChange={(e) => setPublishFilter(e.target.value as any)} className={selectClass}>
                            <option value="all">Semua Publikasi</option>
                            <option value="tayang">Tayang</option>
                            <option value="pending">Pending</option>
                        </select>

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
                    </div>
                </div>

                {/* Table Header */}
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
            </div>

            {/* ============ TABLE BODY ============ */}
            <div className="px-8">
                {isLoading ? (
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
                ) : filteredDramas.length > 0 ? (
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
                                    <p className="text-[13px] font-semibold text-white group-hover:text-cyan-400 transition-colors truncate leading-tight">
                                        {item.title}
                                    </p>
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
                                                <div className="border-t border-zinc-600 my-0.5" />
                                                <button
                                                    onMouseDown={(e) => {
                                                        e.stopPropagation();
                                                        e.preventDefault();
                                                        setMenuOpenId(null);
                                                        handleDelete(item.id);
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
                ) : (
                    <div className="py-24 text-center">
                        <Film size={40} className="mx-auto text-zinc-700 mb-3" />
                        <p className="text-zinc-500">Tidak ada drama ditemukan.</p>
                    </div>
                )}
            </div>
        </div>
    );
}

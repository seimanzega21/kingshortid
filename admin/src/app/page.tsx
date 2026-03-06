"use client";

import { useEffect, useState } from "react";
import { Users, Video, Film, Eye, ShieldCheck, AlertTriangle, XCircle, Activity, Clock, ArrowRight, Wrench, Wifi, Database, Zap } from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

interface DashboardData {
  stats: {
    totalUsers: number;
    activeUsers: number;
    onlineUsers: number;
    totalDramas: number;
    activeDramas: number;
    inactiveDramas: number;
    totalEpisodes: number;
    totalViews: number;
  };
  dataHealth: {
    healthy: number;
    genericGenre: number;
    noDescription: number;
    noCover: number;
    noEpisodes: number;
    deactivated: number;
  };
  recentUsers: Array<{ id: string; name: string; email: string; role: string; createdAt: string }>;
  popularDramas: Array<{ id: string; title: string; cover: string; views: number }>;
  recentDramas: Array<{ id: string; title: string; cover: string; totalEpisodes: number; createdAt: string; genres: string[] }>;
  source?: string;
}

interface HealthData {
  status: string;
  database: { connected: boolean; type: string; latency?: number; error?: string };
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fixingGenres, setFixingGenres] = useState(false);
  const [health, setHealth] = useState<HealthData | null>(null);

  const fetchDashboard = () => {
    fetch("/api/dashboard")
      .then(r => r.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const fetchHealth = () => {
    fetch("/api/health")
      .then(r => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'error', database: { connected: false, type: 'unknown', error: 'Unreachable' } }));
  };

  useEffect(() => {
    fetchDashboard();
    fetchHealth();
  }, []);

  const s = data?.stats;
  const h = data?.dataHealth;
  const dbConnected = health?.database?.connected;

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white">Dashboard</h1>
          <p className="text-zinc-400 mt-1 text-sm">Overview statistik dan data quality KingShort.</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Database Connection Status */}
          <div className={`flex items-center gap-2 rounded-full px-4 py-2 border transition-colors ${health === null
              ? 'bg-zinc-900 border-zinc-800'
              : dbConnected
                ? 'bg-emerald-500/5 border-emerald-500/20'
                : 'bg-red-500/5 border-red-500/20'
            }`}>
            <Database size={14} className={
              health === null ? 'text-zinc-500' : dbConnected ? 'text-emerald-500' : 'text-red-500'
            } />
            <span className={`text-sm font-medium ${health === null ? 'text-zinc-500' : dbConnected ? 'text-emerald-500' : 'text-red-500'
              }`}>
              {health === null ? 'Checking...' : dbConnected ? 'Supabase' : 'DB Error'}
            </span>
            {health?.database?.latency !== undefined && (
              <span className="text-[10px] text-zinc-500 flex items-center gap-0.5">
                <Zap size={8} /> {health.database.latency}ms
              </span>
            )}
          </div>
          {/* Source Badge */}
          {data?.source && (
            <div className="flex items-center gap-2 bg-zinc-900 rounded-full px-4 py-2 border border-zinc-800">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
              </span>
              <span className="text-sm font-medium text-green-500">Live</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {loading ? (
          Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-28 rounded-xl bg-zinc-900" />)
        ) : (
          <>
            <StatCard label="Total Users" value={s?.totalUsers || 0} icon={Users} accent="blue" />
            <StatCard label="User Online" value={s?.onlineUsers || 0} icon={Wifi} accent="green" />
            <StatCard label="Drama Aktif" value={s?.activeDramas || 0} icon={Film} accent="emerald" />
            <StatCard label="Total Episode" value={s?.totalEpisodes || 0} icon={Video} accent="amber" />
            <StatCard label="Total Views" value={s?.totalViews || 0} icon={Eye} accent="cyan" />
          </>
        )}
      </div>

      {/* Data Health Section */}
      {!loading && h && (
        <div className="rounded-xl border border-zinc-800 bg-[#111] p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity size={20} className="text-emerald-500" />
              Data Quality
            </h3>
            <Link href="/scraper" className="text-xs text-cyan-500 hover:text-cyan-400 flex items-center gap-1">
              Detail Audit <ArrowRight size={12} />
            </Link>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <HealthCard label="Healthy" value={h.healthy} color="emerald" icon="✅" />
            <div className="relative">
              <HealthCard label="Genre Generic" value={h.genericGenre} color={h.genericGenre > 0 ? "amber" : "emerald"} icon="🏷️" />
              {h.genericGenre > 0 && (
                <button
                  onClick={async () => {
                    setFixingGenres(true);
                    try {
                      const res = await fetch('/api/dramas/fix-genres', { method: 'POST' });
                      const result = await res.json();
                      toast.success(`${result.updated} drama berhasil di-fix! Sisa ${result.remaining} generic.`);
                      fetchDashboard();
                    } catch { toast.error('Gagal fix genre'); }
                    setFixingGenres(false);
                  }}
                  disabled={fixingGenres}
                  className="absolute top-1 right-1 p-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 transition-colors disabled:opacity-50"
                  title="Auto-fix genres"
                >
                  <Wrench size={12} className={fixingGenres ? 'animate-spin' : ''} />
                </button>
              )}
            </div>
            <HealthCard label="No Description" value={h.noDescription} color={h.noDescription > 0 ? "amber" : "emerald"} icon="📝" />
            <HealthCard label="No Cover" value={h.noCover} color={h.noCover > 0 ? "red" : "emerald"} icon="🖼️" />
            <HealthCard label="Deactivated" value={h.deactivated} color="zinc" icon="🚫" />
          </div>

          {/* Health Bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-zinc-500 mb-1">
              <span>Coverage Score</span>
              <span>{Math.round((h.healthy / Math.max(1, s?.activeDramas || 1)) * 100)}%</span>
            </div>
            <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000"
                style={{ width: `${(h.healthy / Math.max(1, s?.activeDramas || 1)) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Popular Dramas */}
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-[#111] p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-semibold text-white">Drama Terpopuler</h3>
            <Link href="/dramas" className="text-xs text-cyan-500 hover:text-cyan-400">Lihat Semua</Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {loading ? (
              Array(4).fill(0).map((_, i) => <Skeleton key={i} className="aspect-[2/3] rounded-lg" />)
            ) : data?.popularDramas?.length ? (
              data.popularDramas.slice(0, 4).map(d => (
                <Link key={d.id} href={`/dramas/${d.id}`} className="group relative aspect-[2/3] rounded-lg overflow-hidden bg-zinc-800">
                  {d.cover ? (
                    <img src={d.cover} alt={d.title} className="w-full h-full object-cover transition-transform group-hover:scale-110" referrerPolicy="no-referrer" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; (e.target as HTMLImageElement).parentElement!.querySelector('.cover-fallback')?.classList.remove('hidden'); }} />
                  ) : null}
                  <div className={`cover-fallback w-full h-full bg-zinc-800 flex items-center justify-center text-zinc-600 absolute inset-0 ${d.cover ? 'hidden' : ''}`}>No Image</div>
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />
                  <div className="absolute bottom-2 left-2 right-2">
                    <h4 className="text-white font-semibold text-xs truncate">{d.title}</h4>
                    <p className="text-[10px] text-zinc-400 flex items-center gap-1 mt-0.5">
                      <Eye size={9} /> {d.views.toLocaleString()}
                    </p>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-zinc-500 col-span-4">Belum ada data.</p>
            )}
          </div>
        </div>

        {/* Recent Users */}
        <div className="rounded-xl border border-zinc-800 bg-[#111] p-6">
          <h3 className="text-lg font-semibold text-white mb-5">User Terbaru</h3>
          <div className="space-y-4">
            {loading ? (
              Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)
            ) : data?.recentUsers?.length ? (
              data.recentUsers.map(u => (
                <div key={u.id} className="flex gap-3 items-center">
                  <div className="h-8 w-8 rounded-full bg-cyan-600/20 flex items-center justify-center text-cyan-400 font-bold text-xs uppercase flex-shrink-0">
                    {u.name?.substring(0, 2) || '??'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{u.name}</p>
                    <p className="text-xs text-zinc-500 truncate">{u.email}</p>
                  </div>
                  <span className="text-[10px] text-zinc-600 whitespace-nowrap">
                    {new Date(u.createdAt).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-zinc-500">Belum ada user.</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Dramas Added */}
      {!loading && data?.recentDramas?.length ? (
        <div className="rounded-xl border border-zinc-800 bg-[#111] p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Drama Terbaru Ditambahkan</h3>
          <div className="divide-y divide-zinc-800">
            {data.recentDramas.map(d => (
              <Link key={d.id} href={`/dramas/${d.id}`} className="flex items-center gap-4 py-3 hover:bg-zinc-800/50 px-2 rounded-lg transition-colors">
                {d.cover ? (
                  <img src={d.cover} alt={d.title} className="h-12 w-8 rounded object-cover flex-shrink-0" referrerPolicy="no-referrer" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; const fb = document.createElement('div'); fb.className = 'h-12 w-8 rounded bg-zinc-800 flex-shrink-0'; (e.target as HTMLImageElement).parentElement!.insertBefore(fb, e.target as HTMLImageElement); }} />
                ) : (
                  <div className="h-12 w-8 rounded bg-zinc-800 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium text-sm truncate">{d.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {(typeof d.genres === 'string' ? JSON.parse(d.genres || '[]') : (d.genres || [])).slice(0, 2).map((g: string) => (
                      <span key={g} className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">{g}</span>
                    ))}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-xs text-zinc-400">{d.totalEpisodes} eps</p>
                  <p className="text-[10px] text-zinc-600 flex items-center gap-1">
                    <Clock size={9} /> {new Date(d.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function StatCard({ label, value, icon: Icon, accent }: { label: string; value: number; icon: any; accent: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-500' },
    green: { bg: 'bg-green-500/10', text: 'text-green-500' },
    emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-500' },
    amber: { bg: 'bg-amber-500/10', text: 'text-amber-500' },
    cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-500' },
  };
  const c = colors[accent] || colors.blue;
  return (
    <div className="rounded-xl border border-zinc-800 bg-[#111] p-5 hover:border-zinc-700 transition-colors">
      <div className={`p-2 rounded-lg ${c.bg} ${c.text} w-fit`}>
        <Icon size={20} />
      </div>
      <h3 className="text-2xl font-bold text-white mt-3">{value.toLocaleString()}</h3>
      <p className="text-xs text-zinc-500 mt-0.5">{label}</p>
    </div>
  );
}

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

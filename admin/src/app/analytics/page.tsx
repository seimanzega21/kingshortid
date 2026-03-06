"use client";

import { useState, useEffect } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';
import { Download, Calendar, ArrowUpRight, Eye, Users, Film, Coins, Loader2 } from "lucide-react";

interface AnalyticsData {
    viewershipData: Array<{ name: string; date: string; value: number }>;
    userGrowthData: Array<{ name: string; date: string; value: number }>;
    topDramas: Array<{ id: string; title: string; views: number; rating: number; episodes: number }>;
    stats: {
        totalViews: number;
        totalUsers: number;
        totalDramas: number;
        totalRevenue: number;
    };
}

export default function AnalyticsPage() {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [period, setPeriod] = useState('7d');

    useEffect(() => {
        loadAnalytics();
    }, [period]);

    const loadAnalytics = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/analytics?period=${period}`);
            const json = await res.json();
            setData(json);
        } catch (error) {
            console.error('Failed to load analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
        return num.toString();
    };

    if (loading) {
        return (
            <div className="p-8 flex items-center justify-center min-h-screen">
                <Loader2 className="animate-spin text-purple-500" size={48} />
            </div>
        );
    }

    return (
        <div className="p-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Analitik & Laporan</h1>
                    <p className="text-zinc-400 mt-1">Pantau performa bisnis, pertumbuhan pengguna, dan tren konten.</p>
                </div>
                <div className="flex gap-2">
                    <select
                        value={period}
                        onChange={(e) => setPeriod(e.target.value)}
                        className="flex items-center gap-2 bg-[#121212] border border-zinc-800 text-zinc-300 px-4 py-2 rounded-lg text-sm"
                    >
                        <option value="7d">7 Hari Terakhir</option>
                        <option value="30d">30 Hari Terakhir</option>
                        <option value="90d">90 Hari Terakhir</option>
                    </select>
                    <button className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                        <Download size={16} />
                        <span>Export Report</span>
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard title="Total Views" value={formatNumber(data?.stats.totalViews || 0)} icon={Eye} color="text-blue-500" bg="bg-blue-500/10" />
                <StatCard title="Total Users" value={formatNumber(data?.stats.totalUsers || 0)} icon={Users} color="text-green-500" bg="bg-green-500/10" />
                <StatCard title="Total Dramas" value={formatNumber(data?.stats.totalDramas || 0)} icon={Film} color="text-purple-500" bg="bg-purple-500/10" />
                <StatCard title="Total Revenue" value={`Rp ${formatNumber(data?.stats.totalRevenue || 0)}`} icon={Coins} color="text-yellow-500" bg="bg-yellow-500/10" />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Viewership Trend */}
                <div className="rounded-xl border border-zinc-800 bg-[#121212] p-6">
                    <h3 className="text-lg font-semibold text-white mb-6">Tren Penonton</h3>
                    <div className="h-[300px] w-full">
                        {data?.viewershipData && data.viewershipData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={data.viewershipData}>
                                    <defs>
                                        <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis dataKey="name" stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip contentStyle={{ backgroundColor: '#1A1A1A', borderColor: '#333', color: '#fff' }} />
                                    <Area type="monotone" dataKey="value" stroke="#8884d8" fillOpacity={1} fill="url(#colorViews)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-zinc-500">Belum ada data</div>
                        )}
                    </div>
                </div>

                {/* User Growth */}
                <div className="rounded-xl border border-zinc-800 bg-[#121212] p-6">
                    <h3 className="text-lg font-semibold text-white mb-6">Pertumbuhan User</h3>
                    <div className="h-[300px] w-full">
                        {data?.userGrowthData && data.userGrowthData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={data.userGrowthData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis dataKey="name" stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip cursor={{ fill: '#333', opacity: 0.4 }} contentStyle={{ backgroundColor: '#1A1A1A', borderColor: '#333', color: '#fff' }} />
                                    <Bar dataKey="value" fill="#10B981" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-zinc-500">Belum ada data</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Top Content Table */}
            <div className="rounded-xl border border-zinc-800 bg-[#121212] p-6">
                <h3 className="text-lg font-semibold text-white mb-6">Konten Terpopuler</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="text-zinc-500 border-b border-zinc-800">
                            <tr>
                                <th className="pb-3 font-medium">#</th>
                                <th className="pb-3 font-medium">Judul Drama</th>
                                <th className="pb-3 font-medium">Views</th>
                                <th className="pb-3 font-medium">Episodes</th>
                                <th className="pb-3 font-medium text-right">Rating</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800">
                            {data?.topDramas && data.topDramas.length > 0 ? (
                                data.topDramas.map((drama, i) => (
                                    <tr key={drama.id} className="group">
                                        <td className="py-4 text-zinc-500">{i + 1}</td>
                                        <td className="py-4 font-medium text-white">{drama.title}</td>
                                        <td className="py-4 text-zinc-400">{formatNumber(drama.views)}</td>
                                        <td className="py-4 text-zinc-400">{drama.episodes} eps</td>
                                        <td className="py-4 text-right">
                                            <span className="text-yellow-500 flex items-center justify-end gap-1">
                                                ⭐ {drama.rating.toFixed(1)}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="py-8 text-center text-zinc-500">Belum ada data drama</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, icon: Icon, color, bg }: any) {
    return (
        <div className="rounded-xl border border-zinc-800 bg-[#121212] p-6">
            <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${bg} ${color}`}>
                    <Icon size={20} />
                </div>
                <div>
                    <p className="text-sm text-zinc-400">{title}</p>
                    <p className="text-2xl font-bold text-white">{value}</p>
                </div>
            </div>
        </div>
    );
}

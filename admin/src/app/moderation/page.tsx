'use client';

import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, Eye, Search, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface ReportedContent {
    id: string;
    type: 'drama' | 'comment' | 'user';
    targetId: string;
    title: string;
    reason: string;
    status: 'pending' | 'approved' | 'rejected';
    createdAt: string;
    reporter: {
        id: string;
        name: string;
        email: string;
    };
}

interface ReportCounts {
    pending: number;
    approved: number;
    rejected: number;
    total: number;
}

export default function ModerationPage() {
    const [reports, setReports] = useState<ReportedContent[]>([]);
    const [counts, setCounts] = useState<ReportCounts>({ pending: 0, approved: 0, rejected: 0, total: 0 });
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        loadReports();
    }, [filter]);

    const loadReports = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/reports?status=${filter}`);
            const data = await res.json();
            setReports(data.reports || []);
            setCounts(data.counts || { pending: 0, approved: 0, rejected: 0, total: 0 });
        } catch (error) {
            console.error('Failed to load reports:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (id: string, action: 'approve' | 'reject') => {
        try {
            const res = await fetch('/api/reports', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, status: action === 'approve' ? 'approved' : 'rejected' })
            });

            if (res.ok) {
                toast.success(action === 'approve' ? 'Laporan disetujui, konten dihapus' : 'Laporan ditolak');
                loadReports();
            } else {
                toast.error('Gagal memproses laporan');
            }
        } catch {
            toast.error('Gagal memproses laporan');
        }
    };

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'drama': return '🎬';
            case 'comment': return '💬';
            case 'user': return '👤';
            default: return '📄';
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'pending':
                return <span className="px-2 py-1 bg-yellow-500/20 text-yellow-500 text-xs rounded-full">Pending</span>;
            case 'approved':
                return <span className="px-2 py-1 bg-green-500/20 text-green-500 text-xs rounded-full">Approved</span>;
            case 'rejected':
                return <span className="px-2 py-1 bg-red-500/20 text-red-500 text-xs rounded-full">Rejected</span>;
        }
    };

    const filteredReports = reports.filter(r => {
        if (searchQuery && !r.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
    });

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Shield className="text-purple-500" />
                        Content Moderation
                    </h1>
                    <p className="text-zinc-400 mt-1">Kelola laporan konten dan moderasi platform</p>
                </div>
                {counts.pending > 0 && (
                    <div className="px-4 py-2 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
                        <span className="text-yellow-500 font-medium">{counts.pending} laporan menunggu</span>
                    </div>
                )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard icon={AlertTriangle} color="yellow" count={counts.pending} label="Pending" />
                <StatCard icon={CheckCircle} color="green" count={counts.approved} label="Approved" />
                <StatCard icon={XCircle} color="red" count={counts.rejected} label="Rejected" />
                <StatCard icon={Shield} color="purple" count={counts.total} label="Total Reports" />
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                    <input
                        type="text"
                        placeholder="Cari laporan..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2 text-white placeholder:text-zinc-500 focus:outline-none focus:border-purple-500"
                    />
                </div>
                <div className="flex gap-2">
                    {(['all', 'pending', 'approved', 'rejected'] as const).map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f ? 'bg-purple-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-white'
                                }`}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Reports Table */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="animate-spin text-purple-500" size={40} />
                    </div>
                ) : (
                    <>
                        <table className="w-full">
                            <thead className="bg-zinc-800/50">
                                <tr>
                                    <th className="text-left text-sm font-medium text-zinc-400 px-6 py-4">Konten</th>
                                    <th className="text-left text-sm font-medium text-zinc-400 px-6 py-4">Alasan</th>
                                    <th className="text-left text-sm font-medium text-zinc-400 px-6 py-4">Pelapor</th>
                                    <th className="text-left text-sm font-medium text-zinc-400 px-6 py-4">Tanggal</th>
                                    <th className="text-left text-sm font-medium text-zinc-400 px-6 py-4">Status</th>
                                    <th className="text-right text-sm font-medium text-zinc-400 px-6 py-4">Aksi</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800">
                                {filteredReports.map(report => (
                                    <tr key={report.id} className="hover:bg-zinc-800/30 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <span className="text-xl">{getTypeIcon(report.type)}</span>
                                                <div>
                                                    <p className="text-white font-medium">{report.title}</p>
                                                    <p className="text-xs text-zinc-500 capitalize">{report.type}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-zinc-400">{report.reason}</td>
                                        <td className="px-6 py-4 text-zinc-400 text-sm">{report.reporter?.email || 'Unknown'}</td>
                                        <td className="px-6 py-4 text-zinc-500 text-sm">
                                            {new Date(report.createdAt).toLocaleDateString('id-ID')}
                                        </td>
                                        <td className="px-6 py-4">{getStatusBadge(report.status)}</td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center justify-end gap-2">
                                                {report.status === 'pending' && (
                                                    <>
                                                        <button
                                                            onClick={() => handleAction(report.id, 'approve')}
                                                            className="p-2 bg-green-500/20 text-green-500 rounded-lg hover:bg-green-500/30 transition-colors"
                                                            title="Setujui & Hapus Konten"
                                                        >
                                                            <CheckCircle size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => handleAction(report.id, 'reject')}
                                                            className="p-2 bg-red-500/20 text-red-500 rounded-lg hover:bg-red-500/30 transition-colors"
                                                            title="Tolak Laporan"
                                                        >
                                                            <XCircle size={16} />
                                                        </button>
                                                    </>
                                                )}
                                                <button className="p-2 bg-zinc-800 text-zinc-400 rounded-lg hover:text-white transition-colors">
                                                    <Eye size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {filteredReports.length === 0 && (
                            <div className="text-center py-12">
                                <Shield className="mx-auto text-zinc-700 mb-4" size={48} />
                                <p className="text-zinc-500">Tidak ada laporan ditemukan</p>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

function StatCard({ icon: Icon, color, count, label }: { icon: any; color: string; count: number; label: string }) {
    const colors: Record<string, { bg: string; text: string }> = {
        yellow: { bg: 'bg-yellow-500/20', text: 'text-yellow-500' },
        green: { bg: 'bg-green-500/20', text: 'text-green-500' },
        red: { bg: 'bg-red-500/20', text: 'text-red-500' },
        purple: { bg: 'bg-purple-500/20', text: 'text-purple-500' }
    };

    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-3">
                <div className={`p-2 ${colors[color].bg} rounded-lg`}>
                    <Icon className={colors[color].text} size={20} />
                </div>
                <div>
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-sm text-zinc-500">{label}</p>
                </div>
            </div>
        </div>
    );
}

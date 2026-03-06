"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, CheckCircle, XCircle, RefreshCw, Search, ChevronDown, ChevronUp, Wrench } from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

interface AuditResult {
    total: number;
    healthy: number;
    summary: {
        brokenCover: number;
        badDescription: number;
        genericGenre: number;
        noEpisodes: number;
        episodeMismatch: number;
    };
    issues: Array<{
        id: string;
        title: string;
        problems: string[];
        cover: string;
        totalEpisodes: number;
    }>;
    deactivated: Array<{
        id: string;
        title: string;
        cover: string;
        totalEpisodes: number;
    }>;
}

export default function ScraperPage() {
    const [audit, setAudit] = useState<AuditResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState<string>("all");
    const [search, setSearch] = useState("");
    const [showDeactivated, setShowDeactivated] = useState(false);
    const [fixing, setFixing] = useState(false);

    const runAudit = () => {
        setLoading(true);
        fetch("/api/scraper/audit")
            .then(r => r.json())
            .then(setAudit)
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => { runAudit(); }, []);

    const filteredIssues = audit?.issues?.filter(i => {
        if (filter !== "all" && !i.problems.some(p => p.includes(filter))) return false;
        if (search && !i.title.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    }) || [];

    const problemColor: Record<string, string> = {
        NO_COVER: 'bg-red-500/10 text-red-400 border-red-500/20',
        BAD_DESC: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        GENERIC_GENRE: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        NO_EPISODES: 'bg-red-500/10 text-red-400 border-red-500/20',
    };

    const getProblemStyle = (p: string) => {
        for (const [key, style] of Object.entries(problemColor)) {
            if (p.includes(key)) return style;
        }
        return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20';
    };

    return (
        <div className="p-6 lg:p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white">Scraper & Data Quality</h1>
                    <p className="text-zinc-400 mt-1 text-sm">Monitor kualitas data dan audit drama database.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={async () => {
                            setFixing(true);
                            try {
                                const res = await fetch('/api/dramas/fix-issues', { method: 'POST' });
                                const data = await res.json();
                                toast.success(`Fixed ${data.descFixed} descriptions, ${data.genreFixed} genres`);
                                runAudit();
                            } catch { toast.error('Failed to fix issues'); }
                            setFixing(false);
                        }}
                        disabled={fixing || loading || !audit?.issues?.length}
                        className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50"
                    >
                        <Wrench size={16} className={fixing ? 'animate-spin' : ''} />
                        {fixing ? 'Fixing...' : 'Fix All Issues'}
                    </button>
                    <button
                        onClick={runAudit}
                        disabled={loading}
                        className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        {loading ? 'Scanning...' : 'Run Audit'}
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            {loading ? (
                <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                    {Array(6).fill(0).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl bg-zinc-900" />)}
                </div>
            ) : audit && (
                <>
                    <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                        <SummaryCard label="Total Drama" value={audit.total} icon="📊" accent="zinc" />
                        <SummaryCard label="Healthy ✅" value={audit.healthy} icon="✅" accent="emerald" />
                        <SummaryCard label="Cover Rusak" value={audit.summary.brokenCover} icon="🖼️" accent={audit.summary.brokenCover > 0 ? "red" : "emerald"} />
                        <SummaryCard label="Deskripsi Jelek" value={audit.summary.badDescription} icon="📝" accent={audit.summary.badDescription > 0 ? "amber" : "emerald"} />
                        <SummaryCard label="Genre Generic" value={audit.summary.genericGenre} icon="🏷️" accent={audit.summary.genericGenre > 0 ? "amber" : "emerald"} />
                        <SummaryCard label="Episode Mismatch" value={audit.summary.episodeMismatch} icon="📺" accent={audit.summary.episodeMismatch > 0 ? "amber" : "emerald"} />
                    </div>

                    {/* Health Score Bar */}
                    <div className="rounded-xl border border-zinc-800 bg-[#111] p-5">
                        <div className="flex items-center justify-between text-sm mb-2">
                            <span className="text-zinc-400 font-medium">Data Quality Score</span>
                            <span className="text-emerald-400 font-bold">
                                {Math.round((audit.healthy / Math.max(1, audit.total)) * 100)}%
                            </span>
                        </div>
                        <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000"
                                style={{ width: `${(audit.healthy / Math.max(1, audit.total)) * 100}%` }}
                            />
                        </div>
                        <div className="flex items-center gap-4 mt-3 text-xs text-zinc-500">
                            <span className="flex items-center gap-1">
                                <span className="h-2 w-2 rounded-full bg-emerald-500" /> Healthy: {audit.healthy}
                            </span>
                            <span className="flex items-center gap-1">
                                <span className="h-2 w-2 rounded-full bg-amber-500" /> Issues: {audit.issues.length}
                            </span>
                            <span className="flex items-center gap-1">
                                <span className="h-2 w-2 rounded-full bg-zinc-600" /> Deactivated: {audit.deactivated.length}
                            </span>
                        </div>
                    </div>

                    {/* Issues Table */}
                    <div className="rounded-xl border border-zinc-800 bg-[#111]">
                        <div className="p-5 border-b border-zinc-800">
                            <div className="flex flex-col md:flex-row gap-3 justify-between">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <AlertTriangle size={18} className="text-amber-500" />
                                    Drama dengan Issues ({filteredIssues.length})
                                </h3>
                                <div className="flex gap-2">
                                    <div className="relative">
                                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" size={14} />
                                        <input
                                            type="text"
                                            placeholder="Cari..."
                                            className="bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-3 py-1.5 text-sm text-white w-48 focus:outline-none focus:border-cyan-500"
                                            value={search}
                                            onChange={e => setSearch(e.target.value)}
                                        />
                                    </div>
                                    <select
                                        className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-sm text-white"
                                        value={filter}
                                        onChange={e => setFilter(e.target.value)}
                                    >
                                        <option value="all">Semua Issues</option>
                                        <option value="NO_COVER">Cover Rusak</option>
                                        <option value="BAD_DESC">Deskripsi Jelek</option>
                                        <option value="GENERIC_GENRE">Genre Generic</option>
                                        <option value="NO_EPISODES">No Episodes</option>
                                        <option value="EP_MISMATCH">Episode Mismatch</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div className="divide-y divide-zinc-800 max-h-[500px] overflow-y-auto">
                            {filteredIssues.map(issue => (
                                <Link
                                    key={issue.id}
                                    href={`/dramas/${issue.id}`}
                                    className="flex items-center gap-4 p-4 hover:bg-zinc-800/50 transition-colors"
                                >
                                    {issue.cover ? (
                                        <img src={issue.cover} alt="" className="h-10 w-7 rounded object-cover flex-shrink-0 bg-zinc-800" referrerPolicy="no-referrer" />
                                    ) : (
                                        <div className="h-10 w-7 rounded bg-zinc-800 flex-shrink-0" />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-white font-medium text-sm truncate">{issue.title}</p>
                                        <p className="text-[10px] text-zinc-500">{issue.totalEpisodes} episodes</p>
                                    </div>
                                    <div className="flex flex-wrap gap-1 justify-end">
                                        {issue.problems.map((p, i) => (
                                            <span key={i} className={`text-[10px] px-2 py-0.5 rounded-full border ${getProblemStyle(p)}`}>
                                                {p.replace(/_/g, ' ')}
                                            </span>
                                        ))}
                                    </div>
                                </Link>
                            ))}
                            {filteredIssues.length === 0 && (
                                <div className="p-8 text-center text-zinc-500">
                                    <CheckCircle className="mx-auto mb-2 text-emerald-500" size={32} />
                                    <p>Semua drama healthy! 🎉</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Deactivated Dramas Section */}
                    {audit.deactivated.length > 0 && (
                        <div className="rounded-xl border border-zinc-800 bg-[#111]">
                            <button
                                onClick={() => setShowDeactivated(!showDeactivated)}
                                className="w-full flex items-center justify-between p-5"
                            >
                                <h3 className="text-lg font-semibold text-zinc-400 flex items-center gap-2">
                                    <XCircle size={18} className="text-zinc-500" />
                                    Deactivated Dramas ({audit.deactivated.length})
                                </h3>
                                {showDeactivated ? <ChevronUp size={18} className="text-zinc-500" /> : <ChevronDown size={18} className="text-zinc-500" />}
                            </button>
                            {showDeactivated && (
                                <div className="divide-y divide-zinc-800 border-t border-zinc-800">
                                    {audit.deactivated.map(d => (
                                        <Link key={d.id} href={`/dramas/${d.id}`} className="flex items-center gap-3 p-3 px-5 hover:bg-zinc-800/50 transition-colors">
                                            <div className="h-8 w-6 rounded bg-zinc-800 flex-shrink-0 overflow-hidden">
                                                {d.cover && <img src={d.cover} className="w-full h-full object-cover opacity-50" referrerPolicy="no-referrer" />}
                                            </div>
                                            <span className="text-sm text-zinc-500">{d.title}</span>
                                            <span className="text-xs text-zinc-600 ml-auto">{d.totalEpisodes} eps</span>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

function SummaryCard({ label, value, icon, accent }: { label: string; value: number; icon: string; accent: string }) {
    const borders: Record<string, string> = {
        emerald: 'border-emerald-500/20',
        amber: 'border-amber-500/20',
        red: 'border-red-500/20',
        zinc: 'border-zinc-700',
    };
    const texts: Record<string, string> = {
        emerald: 'text-emerald-400',
        amber: 'text-amber-400',
        red: 'text-red-400',
        zinc: 'text-white',
    };
    return (
        <div className={`rounded-xl border bg-[#111] p-4 ${borders[accent] || borders.zinc}`}>
            <div className="flex items-center justify-between">
                <span className="text-lg">{icon}</span>
                <span className={`text-2xl font-bold ${texts[accent] || texts.zinc}`}>{value}</span>
            </div>
            <p className="text-[11px] text-zinc-500 mt-1">{label}</p>
        </div>
    );
}

"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Users, Ban, CheckCircle2, Trash2, AlertTriangle, UserX, Chrome } from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

interface User {
    id: string;
    name: string;
    email: string;
    role: string;
    isActive: boolean;
    isGuest: boolean;
    provider: string;
    coins: number;
    createdAt: string;
}

export default function UserManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [filterRole, setFilterRole] = useState("");
    const [filterAccountType, setFilterAccountType] = useState("");
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    // Selection state
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [confirmAction, setConfirmAction] = useState<null | "selected" | "all" | string>(null);
    const [deleting, setDeleting] = useState(false);

    const fetchUsers = useCallback(async () => {
        setIsLoading(true);
        try {
            const params = new URLSearchParams();
            params.set("page", page.toString());
            if (searchTerm) params.set("q", searchTerm);
            if (filterRole) params.set("role", filterRole);
            if (filterAccountType) params.set("accountType", filterAccountType);

            const res = await fetch(`/api/users?${params.toString()}`);
            const data = await res.json();

            if (data.users) setUsers(data.users);
            if (data.pages) setTotalPages(data.pages);
            if (data.total != null) setTotalCount(data.total);
        } catch (error) {
            toast.error("Gagal mengambil data user");
        } finally {
            setIsLoading(false);
        }
    }, [page, searchTerm, filterRole, filterAccountType]);

    useEffect(() => {
        const timeout = setTimeout(() => fetchUsers(), 500);
        return () => clearTimeout(timeout);
    }, [fetchUsers]);

    // Toggle single selection
    const toggleSelect = (id: string) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    };

    // Toggle all on current page
    const toggleSelectAll = () => {
        const nonAdminUsers = users.filter(u => u.role !== "admin");
        if (selectedIds.size === nonAdminUsers.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(nonAdminUsers.map(u => u.id)));
        }
    };

    // Handle status change (ban/unban)
    const handleStatusChange = async (userId: string, currentStatus: boolean) => {
        try {
            const res = await fetch(`/api/users/${userId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ isActive: !currentStatus })
            });
            if (res.ok) {
                toast.success(currentStatus ? "User Disabled" : "User Activated");
                fetchUsers();
            } else throw new Error();
        } catch { toast.error("Error updating status"); }
    };

    // Handle single delete
    const handleDeleteOne = async (userId: string) => {
        setDeleting(true);
        try {
            const res = await fetch(`/api/users/${userId}`, { method: "DELETE" });
            if (res.ok) {
                toast.success("User berhasil dihapus");
                setSelectedIds(prev => { const n = new Set(prev); n.delete(userId); return n; });
                fetchUsers();
            } else {
                const data = await res.json();
                toast.error(data.message || "Gagal menghapus user");
            }
        } catch { toast.error("Gagal menghapus user"); }
        setDeleting(false);
        setConfirmAction(null);
    };

    // Handle bulk delete (selected)
    const handleDeleteSelected = async () => {
        if (selectedIds.size === 0) return;
        setDeleting(true);
        try {
            const res = await fetch("/api/users/bulk-delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userIds: Array.from(selectedIds) }),
            });
            const data = await res.json();
            toast.success(`${data.count} user berhasil dihapus`);
            setSelectedIds(new Set());
            fetchUsers();
        } catch { toast.error("Gagal menghapus user"); }
        setDeleting(false);
        setConfirmAction(null);
    };

    // Handle delete all
    const handleDeleteAll = async () => {
        setDeleting(true);
        try {
            const res = await fetch("/api/users/bulk-delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ deleteAll: true }),
            });
            const data = await res.json();
            toast.success(`${data.count} user berhasil dihapus`);
            setSelectedIds(new Set());
            fetchUsers();
        } catch { toast.error("Gagal menghapus user"); }
        setDeleting(false);
        setConfirmAction(null);
    };

    const nonAdminUsers = users.filter(u => u.role !== "admin");
    const allNonAdminSelected = nonAdminUsers.length > 0 && selectedIds.size === nonAdminUsers.length;

    // Helper for smart pagination
    const getVisiblePages = () => {
        if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
        if (page <= 4) return [1, 2, 3, 4, 5, '...', totalPages];
        if (page >= totalPages - 3) return [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
        return [1, '...', page - 1, page, page + 1, '...', totalPages];
    };

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-full overflow-hidden">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="space-y-2">
                    <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-200 to-zinc-500">
                        Manajemen Pengguna
                    </h1>
                    <p className="text-zinc-400 text-sm md:text-base">Pantau, kelola, dan atur akses semua pengguna KingShort.</p>
                </div>
                
                <div className="flex items-center gap-4 bg-gradient-to-br from-zinc-900/80 to-[#121212] border border-zinc-800/80 rounded-2xl px-6 py-4 shadow-2xl backdrop-blur-md relative overflow-hidden group">
                    <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-xl relative z-10 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
                        <Users size={22} className="text-cyan-400" />
                    </div>
                    <div className="relative z-10">
                        <p className="text-[11px] text-zinc-500 font-bold uppercase tracking-widest mb-1">Total Pengguna</p>
                        <p className="text-2xl font-black text-white drop-shadow-md">{totalCount.toLocaleString()}</p>
                    </div>
                </div>
            </div>

            {/* Filters & Actions Bar */}
            <div className="flex flex-col xl:flex-row gap-4 justify-between bg-zinc-900/40 backdrop-blur-md p-2.5 rounded-2xl border border-zinc-800 shadow-inner">
                <div className="flex flex-wrap gap-2.5 flex-1 items-center">
                    <div className="relative flex-1 min-w-[200px] max-w-sm">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
                        <input
                            type="text"
                            placeholder="Cari email atau nama..."
                            className="w-full bg-black/40 border border-zinc-700/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:bg-zinc-800/50 transition-all placeholder:text-zinc-600"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex gap-2.5 flex-1 sm:flex-none">
                        <select
                            value={filterRole}
                            onChange={(e) => setFilterRole(e.target.value)}
                            className="flex-1 sm:flex-none bg-black/40 border border-zinc-700/50 text-zinc-300 text-sm rounded-xl px-4 py-2.5 outline-none focus:border-cyan-500/50 hover:bg-zinc-800/50 cursor-pointer transition-colors"
                        >
                            <option value="">Semua Role</option>
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                        </select>
                        <select
                            value={filterAccountType}
                            onChange={(e) => setFilterAccountType(e.target.value)}
                            className="flex-1 sm:flex-none bg-black/40 border border-zinc-700/50 text-zinc-300 text-sm rounded-xl px-4 py-2.5 outline-none focus:border-cyan-500/50 hover:bg-zinc-800/50 cursor-pointer transition-colors"
                        >
                            <option value="">Semua Akun</option>
                            <option value="guest">🎭 Tamu</option>
                            <option value="google">🔵 Google</option>
                            <option value="registered">📧 Terdaftar</option>
                        </select>
                    </div>
                </div>

                {/* Bulk Actions */}
                <div className="flex flex-wrap gap-2.5 items-center px-1">
                    {selectedIds.size > 0 && (
                        <button
                            onClick={() => setConfirmAction("selected")}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white border border-red-500/20 text-sm font-semibold transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                        >
                            <Trash2 size={16} /> Hapus ({selectedIds.size})
                        </button>
                    )}
                    <button
                        onClick={() => setConfirmAction("all")}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-800/60 text-zinc-400 hover:bg-red-500 hover:text-white border border-zinc-700/50 text-sm font-semibold transition-all hover:border-red-500/50"
                    >
                        <AlertTriangle size={16} /> Hapus Semua
                    </button>
                </div>
            </div>

            {/* User Table */}
            <div className="rounded-2xl border border-zinc-800/60 bg-[#121212]/80 backdrop-blur-sm overflow-hidden shadow-xl">
                <div className="overflow-x-auto w-full">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                    <thead className="bg-[#1A1A1A] border-b border-zinc-800 text-xs uppercase text-zinc-500">
                        <tr>
                            <th className="px-4 py-4 w-10">
                                <input
                                    type="checkbox"
                                    checked={allNonAdminSelected}
                                    onChange={toggleSelectAll}
                                    className="rounded border-zinc-600 bg-zinc-800 text-cyan-500 focus:ring-cyan-500"
                                />
                            </th>
                            <th className="px-4 py-4 font-semibold">Pengguna</th>
                            <th className="px-4 py-4 font-semibold">Tipe</th>
                            <th className="px-4 py-4 font-semibold">Role</th>
                            <th className="px-4 py-4 font-semibold">Status</th>
                            <th className="px-4 py-4 font-semibold">Koin</th>
                            <th className="px-4 py-4 font-semibold">Bergabung</th>
                            <th className="px-4 py-4 text-right font-semibold">Aksi</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                        {isLoading ? (
                            Array(5).fill(0).map((_, i) => (
                                <tr key={i}>
                                    <td className="px-4 py-4"><Skeleton className="h-4 w-4" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-10 w-48" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-6 w-16" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-6 w-16" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-6 w-16" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-6 w-12" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-6 w-20" /></td>
                                    <td className="px-4 py-4"><Skeleton className="h-8 w-16 ml-auto" /></td>
                                </tr>
                            ))
                        ) : users.length > 0 ? (
                            users.map((user) => (
                                <tr key={user.id} className={`group hover:bg-zinc-800/50 transition-colors ${selectedIds.has(user.id) ? 'bg-cyan-500/5' : ''}`}>
                                    <td className="px-4 py-4">
                                        {user.role !== "admin" ? (
                                            <input
                                                type="checkbox"
                                                checked={selectedIds.has(user.id)}
                                                onChange={() => toggleSelect(user.id)}
                                                className="rounded border-zinc-600 bg-zinc-800 text-cyan-500 focus:ring-cyan-500"
                                            />
                                        ) : (
                                            <span className="text-zinc-700 text-xs">—</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-4">
                                        <Link href={`/users/${user.id}`} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                                            <div className="h-9 w-9 rounded-full bg-cyan-600/20 flex items-center justify-center text-cyan-400 font-bold text-xs uppercase flex-shrink-0">
                                                {user.name?.substring(0, 2) || '??'}
                                            </div>
                                            <div className="min-w-0">
                                                <p className="font-semibold text-white truncate">{user.name}</p>
                                                <p className="text-zinc-500 text-xs truncate">{user.email}</p>
                                            </div>
                                        </Link>
                                    </td>
                                    <td className="px-4 py-4">
                                        {user.isGuest ? (
                                            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-orange-500/10 text-orange-400 border-orange-500/20 w-fit">
                                                <UserX size={12} /> Tamu
                                            </span>
                                        ) : user.provider === 'google' ? (
                                            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-blue-500/10 text-blue-400 border-blue-500/20 w-fit">
                                                <Chrome size={12} /> Google
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 w-fit">
                                                ✉️ Email
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-4 py-4">
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${user.role === 'admin'
                                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                            : 'bg-zinc-800 text-zinc-300 border-zinc-700'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4">
                                        {user.isActive ? (
                                            <div className="flex items-center gap-1.5 text-green-500 text-xs font-medium">
                                                <CheckCircle2 size={13} /> Active
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-1.5 text-red-500 text-xs font-medium">
                                                <Ban size={13} /> Disabled
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-4 py-4">
                                        <span className="text-amber-400 text-xs font-medium">{user.coins?.toLocaleString() || 0}</span>
                                    </td>
                                    <td className="px-4 py-4">
                                        <span className="text-zinc-500 text-xs">{new Date(user.createdAt).toLocaleDateString('id-ID')}</span>
                                    </td>
                                    <td className="px-4 py-4 text-right">
                                        <div className="flex justify-end gap-1">
                                            <button
                                                onClick={() => handleStatusChange(user.id, user.isActive)}
                                                className={`p-1.5 rounded-lg transition-colors ${user.isActive
                                                    ? 'text-zinc-400 hover:bg-red-500/10 hover:text-red-500'
                                                    : 'text-red-500 hover:bg-green-500/10 hover:text-green-500'
                                                    }`}
                                                title={user.isActive ? "Ban User" : "Activate User"}
                                            >
                                                {user.isActive ? <Ban size={15} /> : <CheckCircle2 size={15} />}
                                            </button>
                                            {user.role !== "admin" && (
                                                <button
                                                    onClick={() => setConfirmAction(user.id)}
                                                    className="p-1.5 rounded-lg text-zinc-500 hover:bg-red-500/10 hover:text-red-500 transition-colors"
                                                    title="Hapus Permanen"
                                                >
                                                    <Trash2 size={15} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={8} className="px-6 py-12 text-center text-zinc-500">
                                    Tidak ada pengguna ditemukan.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="p-4 bg-[#161616] border-t border-zinc-800/80 flex flex-col sm:flex-row gap-4 items-center justify-between overflow-x-auto">
                        <span className="text-xs font-medium text-zinc-500 tracking-wide uppercase whitespace-nowrap">
                            Halaman <span className="text-zinc-300">{page}</span> dari {totalPages}
                        </span>
                        <div className="flex items-center gap-1.5">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all bg-zinc-800/30 hover:bg-zinc-800 text-zinc-400 disabled:opacity-30 disabled:hover:bg-zinc-800/30"
                            >
                                ← Prev
                            </button>
                            
                            <div className="flex gap-1">
                                {getVisiblePages().map((p, i) => (
                                    <button
                                        key={i}
                                        onClick={() => typeof p === 'number' && setPage(p)}
                                        disabled={p === '...'}
                                        className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                            p === '...' 
                                                ? 'text-zinc-600 cursor-default px-2' 
                                                : page === p
                                                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-inner'
                                                    : 'bg-zinc-800/50 hover:bg-zinc-700 text-zinc-400 border border-transparent'
                                            }`}
                                    >
                                        {p}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all bg-zinc-800/30 hover:bg-zinc-800 text-zinc-400 disabled:opacity-30 disabled:hover:bg-zinc-800/30"
                            >
                                Next →
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Confirmation Modal */}
            {confirmAction && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => !deleting && setConfirmAction(null)}>
                    <div className="bg-[#1A1A1A] border border-zinc-700 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 rounded-full bg-red-500/10">
                                <AlertTriangle size={24} className="text-red-500" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Konfirmasi Hapus</h3>
                                <p className="text-zinc-400 text-sm mt-0.5">
                                    {confirmAction === "all"
                                        ? "Semua user (kecuali admin) akan dihapus permanen."
                                        : confirmAction === "selected"
                                            ? `${selectedIds.size} user terpilih akan dihapus permanen.`
                                            : "User ini akan dihapus permanen."}
                                </p>
                            </div>
                        </div>

                        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 mb-5">
                            <p className="text-red-400 text-xs">
                                ⚠️ Tindakan ini tidak dapat dibatalkan. Data user akan hilang selamanya.
                            </p>
                        </div>

                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setConfirmAction(null)}
                                disabled={deleting}
                                className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 text-sm font-medium transition-colors disabled:opacity-50"
                            >
                                Batal
                            </button>
                            <button
                                onClick={() => {
                                    if (confirmAction === "all") handleDeleteAll();
                                    else if (confirmAction === "selected") handleDeleteSelected();
                                    else handleDeleteOne(confirmAction);
                                }}
                                disabled={deleting}
                                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                            >
                                {deleting ? (
                                    <>
                                        <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Menghapus...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 size={14} /> Hapus Permanen
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

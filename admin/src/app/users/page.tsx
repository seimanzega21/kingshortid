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
            if (data.total) setTotalCount(data.total);
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

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Manajemen Pengguna</h1>
                    <p className="text-zinc-400 mt-1">Kelola, pantau, dan atur akses pengguna platform KingShort.</p>
                </div>
                <div className="text-sm text-zinc-500">
                    Total: <span className="text-white font-semibold">{totalCount}</span> pengguna
                </div>
            </div>

            {/* Filters & Actions Bar */}
            <div className="flex flex-col md:flex-row gap-4 justify-between bg-[#121212] p-4 rounded-xl border border-zinc-800">
                <div className="flex gap-3 flex-1">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                        <input
                            type="text"
                            placeholder="Cari email atau nama..."
                            className="w-full bg-black/50 border border-zinc-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 transition-colors"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <select
                        value={filterRole}
                        onChange={(e) => setFilterRole(e.target.value)}
                        className="bg-black/50 border border-zinc-700 text-zinc-400 text-sm rounded-lg px-4 py-2 outline-none focus:border-cyan-500"
                    >
                        <option value="">Semua Role</option>
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                    </select>
                    <select
                        value={filterAccountType}
                        onChange={(e) => setFilterAccountType(e.target.value)}
                        className="bg-black/50 border border-zinc-700 text-zinc-400 text-sm rounded-lg px-4 py-2 outline-none focus:border-cyan-500"
                    >
                        <option value="">Semua Tipe Akun</option>
                        <option value="guest">🎭 Tamu</option>
                        <option value="google">🔵 Google</option>
                        <option value="registered">📧 Terdaftar</option>
                    </select>
                </div>

                {/* Bulk Actions */}
                <div className="flex gap-2">
                    {selectedIds.size > 0 && (
                        <button
                            onClick={() => setConfirmAction("selected")}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 text-sm font-medium transition-colors"
                        >
                            <Trash2 size={14} /> Hapus Terpilih ({selectedIds.size})
                        </button>
                    )}
                    <button
                        onClick={() => setConfirmAction("all")}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 text-zinc-400 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20 border border-zinc-700 text-sm font-medium transition-colors"
                    >
                        <Trash2 size={14} /> Hapus Semua
                    </button>
                </div>
            </div>

            {/* User Table */}
            <div className="rounded-xl border border-zinc-800 bg-[#121212] overflow-hidden">
                <table className="w-full text-left text-sm">
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

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="p-4 border-t border-zinc-800 flex items-center justify-between">
                        <span className="text-xs text-zinc-500">
                            Halaman {page} dari {totalPages}
                        </span>
                        <div className="flex gap-1">
                            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                                <button
                                    key={p}
                                    onClick={() => setPage(p)}
                                    className={`px-3 py-1 rounded text-sm ${page === p
                                        ? 'bg-cyan-600 text-white'
                                        : 'hover:bg-zinc-800 text-zinc-400'
                                        }`}
                                >
                                    {p}
                                </button>
                            ))}
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

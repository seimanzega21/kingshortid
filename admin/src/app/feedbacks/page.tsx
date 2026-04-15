"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format } from "date-fns";
import { id } from "date-fns/locale";
import { CheckCircle2, Circle, MessageSquare } from "lucide-react";
import { Toaster, toast } from "sonner";

interface Feedback {
    id: string;
    message: string;
    status: 'unread' | 'read' | 'resolved';
    createdAt: string;
    user: {
        id: string;
        name: string;
        email: string;
    } | null;
}

export default function FeedbacksPage() {
    const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchFeedbacks = async () => {
        try {
            const res = await api.get('/admin/feedbacks');
            setFeedbacks(res.data.feedbacks || []);
        } catch (error) {
            console.error(error);
            toast.error("Gagal memanggil data kotak saran");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchFeedbacks();
    }, []);

    const markAsRead = async (feedbackId: string, currentStatus: string) => {
        if (currentStatus === 'read') return;
        
        try {
            await api.put(`/admin/feedbacks/${feedbackId}`, { status: 'read' });
            // Optimistic update
            setFeedbacks(feedbacks.map(f => f.id === feedbackId ? { ...f, status: 'read' } : f));
            toast.success("Pesan ditandai sudah dibaca");
        } catch (error) {
            console.error(error);
            toast.error("Gagal memperbarui status pesan");
        }
    };

    return (
        <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <MessageSquare className="h-8 w-8 text-yellow-500" />
                        Kotak Saran & Keluhan
                    </h1>
                    <p className="mt-2 text-zinc-400">
                        Baca pesan keluhan dan saran dari pengguna aplikasi mobile.
                    </p>
                </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-zinc-400">
                        <thead className="bg-zinc-950 text-xs uppercase text-zinc-500">
                            <tr>
                                <th className="px-6 py-4">Tanggal Masuk</th>
                                <th className="px-6 py-4">Pengguna</th>
                                <th className="px-6 py-4">Pesan Keluhan</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center">
                                        Memuat data...
                                    </td>
                                </tr>
                            ) : feedbacks.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center">
                                        Belum ada pesan saran atau keluhan dari pengguna.
                                    </td>
                                </tr>
                            ) : (
                                feedbacks.map((item) => (
                                    <tr 
                                        key={item.id} 
                                        className={`border-b border-zinc-800 transition-colors ${item.status === 'unread' ? 'bg-zinc-800/20' : 'hover:bg-zinc-800/50'}`}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {format(new Date(item.createdAt), 'dd MMM yyyy, HH:mm', { locale: id })}
                                        </td>
                                        <td className="px-6 py-4">
                                            {item.user ? (
                                                <div>
                                                    <div className="text-white font-medium">{item.user.name}</div>
                                                    <div className="text-xs">{item.user.email}</div>
                                                </div>
                                            ) : (
                                                <span className="text-zinc-500">Anonim (Terhapus)</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className={`max-w-md ${item.status === 'unread' ? 'text-white font-medium' : 'text-zinc-300'}`}>
                                                {item.message}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                                                item.status === 'unread' 
                                                ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20' 
                                                : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                                            }`}>
                                                {item.status === 'unread' ? <Circle className="h-3 w-3 fill-yellow-500" /> : <CheckCircle2 className="h-3 w-3" />}
                                                {item.status === 'unread' ? 'Belum Dibaca' : 'Sudah Dibaca'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {item.status === 'unread' && (
                                                <button
                                                    onClick={() => markAsRead(item.id, item.status)}
                                                    className="text-sm text-yellow-500 hover:text-yellow-400 hover:underline"
                                                >
                                                    Tandai Dibaca
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
            <Toaster richColors position="top-center" theme="dark" />
        </div>
    );
}

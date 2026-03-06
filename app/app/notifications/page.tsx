"use client";

import { MobileLayout } from "@/components/MobileLayout";
import { ChevronLeft, Bell, Star, Ticket, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";

interface Notification {
    id: string;
    title: string;
    body: string;
    type: string;
    data: any;
    read: boolean;
    createdAt: string;
}

export default function NotificationsPage() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchNotifications();
    }, []);

    const fetchNotifications = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetch('/api/user/notifications');

            if (!response.ok) {
                throw new Error('Failed to fetch notifications');
            }

            const data = await response.json();
            setNotifications(data);
        } catch (err) {
            console.error('Error fetching notifications:', err);
            setError('Gagal memuat notifikasi');
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (notificationId: string) => {
        try {
            const response = await fetch('/api/user/notifications', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notificationId })
            });

            if (response.ok) {
                // Update local state
                setNotifications(prev =>
                    prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
                );
            }
        } catch (err) {
            console.error('Error marking notification as read:', err);
        }
    };

    const markAllAsRead = async () => {
        try {
            const response = await fetch('/api/user/notifications', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ markAllRead: true })
            });

            if (response.ok) {
                // Update all notifications to read
                setNotifications(prev =>
                    prev.map(n => ({ ...n, read: true }))
                );
            }
        } catch (err) {
            console.error('Error marking all as read:', err);
        }
    };

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'new_episode': return Bell;
            case 'coin_reward': return Ticket;
            case 'system': return Star;
            default: return Bell;
        }
    };

    const getNotificationColor = (type: string) => {
        switch (type) {
            case 'new_episode': return 'bg-blue-500';
            case 'coin_reward': return 'bg-yellow-500';
            case 'system': return 'bg-purple-500';
            default: return 'bg-gray-500';
        }
    };

    const getRelativeTime = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    };

    return (
        <MobileLayout showNav={false}>
            <div className="min-h-screen bg-black text-white p-6">

                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/profile" className="p-2 -ml-2 text-gray-400 hover:text-white bg-zinc-900 rounded-full">
                        <ChevronLeft size={24} />
                    </Link>
                    <h1 className="text-xl font-bold">Notifikasi</h1>
                    {!loading && notifications.length > 0 && (
                        <button
                            onClick={markAllAsRead}
                            className="ml-auto text-xs text-yellow-500 hover:text-yellow-400 font-bold transition-colors"
                        >
                            Mark all read
                        </button>
                    )}
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="flex flex-col items-center justify-center py-16">
                        <Loader2 className="w-8 h-8 animate-spin text-yellow-500 mb-4" />
                        <p className="text-gray-400 text-sm">Memuat notifikasi...</p>
                    </div>
                )}

                {/* Error State */}
                {error && !loading && (
                    <div className="flex flex-col items-center justify-center py-16">
                        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                            <Bell className="w-8 h-8 text-red-500" />
                        </div>
                        <p className="text-red-400 text-sm mb-2">{error}</p>
                        <button
                            onClick={fetchNotifications}
                            className="text-xs text-yellow-500 hover:text-yellow-400 font-medium"
                        >
                            Coba lagi
                        </button>
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && notifications.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-16">
                        <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
                            <Bell className="w-8 h-8 text-gray-500" />
                        </div>
                        <p className="text-gray-400 text-sm">Belum ada notifikasi</p>
                    </div>
                )}

                {/* Notification List */}
                {!loading && !error && notifications.length > 0 && (
                    <div className="space-y-4">
                        {notifications.map((notif) => {
                            const Icon = getNotificationIcon(notif.type);
                            const color = getNotificationColor(notif.type);

                            return (
                                <div
                                    key={notif.id}
                                    className="flex gap-4 p-4 bg-zinc-900/50 rounded-2xl border border-zinc-900 relative cursor-pointer hover:bg-zinc-900/70 transition-colors"
                                    onClick={() => !notif.read && markAsRead(notif.id)}
                                >
                                    {/* Unread dot */}
                                    {!notif.read && <div className="absolute top-4 right-4 w-2 h-2 rounded-full bg-red-500" />}

                                    <div className={`w-12 h-12 rounded-full ${color} bg-opacity-10 flex items-center justify-center shrink-0`}>
                                        <Icon size={20} className="text-white" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-sm mb-1">{notif.title}</h3>
                                        <p className="text-gray-400 text-xs mb-2 leading-relaxed">{notif.body}</p>
                                        <span className="text-[10px] text-zinc-600 font-medium bg-zinc-800 px-2 py-0.5 rounded-full">
                                            {getRelativeTime(notif.createdAt)}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

            </div>
        </MobileLayout>
    );
}

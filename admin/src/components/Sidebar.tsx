"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Film,
    Users,
    BarChart3,
    Settings,
    LogOut,
    Clapperboard,
    Tags,
    MessageSquare,
    ChevronRight,
    DollarSign,
    Shield,
    Activity
} from "lucide-react";
import { cn } from "@/lib/utils";

const menuItems = [
    {
        title: "Dashboard",
        icon: LayoutDashboard,
        href: "/",
    },
    {
        title: "Manajemen Drama",
        icon: Film,
        href: "/dramas",
    },
    {
        title: "Genre & Kategori",
        icon: Tags,
        href: "/categories",
    },
    {
        title: "Scraper Monitor",
        icon: Activity,
        href: "/scraper",
    },
    {
        title: "Pengguna",
        icon: Users,
        href: "/users",
    },
    {
        title: "Moderasi",
        icon: Shield,
        href: "/moderation",
    },
    {
        title: "Analitik",
        icon: BarChart3,
        href: "/analytics",
    },
];


const secondaryItems = [
    {
        title: "Monetisasi",
        icon: DollarSign,
        href: "/settings/monetization",
    },
    {
        title: "Pengaturan",
        icon: Settings,
        href: "/settings",
    },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="h-screen w-64 border-r border-zinc-800 bg-black text-white flex-shrink-0">
            <div className="flex h-16 items-center border-b border-zinc-800 px-6">
                <div className="flex items-center gap-2 font-bold text-xl text-yellow-500">
                    <Film className="h-6 w-6" />
                    <span>KingShort</span>
                </div>
            </div>

            <div className="flex h-[calc(100vh-64px)] flex-col justify-between overflow-y-auto py-6">
                <div className="space-y-6 px-4">
                    <div>
                        <div className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                            Menu Utama
                        </div>
                        <nav className="space-y-1">
                            {menuItems.map((item) => (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                                        pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
                                            ? "bg-yellow-500/10 text-yellow-500"
                                            : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                                    )}
                                >
                                    <item.icon className="h-5 w-5" />
                                    <span>{item.title}</span>
                                </Link>
                            ))}
                        </nav>
                    </div>

                    <div>
                        <div className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                            Lainnya
                        </div>
                        <nav className="space-y-1">
                            {secondaryItems.map((item) => (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                                        pathname === item.href
                                            ? "bg-yellow-500/10 text-yellow-500"
                                            : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                                    )}
                                >
                                    <item.icon className="h-5 w-5" />
                                    <span>{item.title}</span>
                                </Link>
                            ))}
                            <button
                                className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-500/10"
                                onClick={() => {/* Logout logic */ }}
                            >
                                <LogOut className="h-5 w-5" />
                                <span>Logout</span>
                            </button>
                        </nav>
                    </div>
                </div>

                <div className="px-6">
                    <div className="flex items-center gap-3 rounded-xl bg-zinc-900 p-4 border border-zinc-800">
                        <div className="h-10 w-10 rounded-full bg-yellow-500/20 flex items-center justify-center text-yellow-500 font-bold">
                            A
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="truncate text-sm font-medium text-white">Admin User</p>
                            <p className="truncate text-xs text-zinc-500">admin@kingshort.com</p>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    );
}

"use client";

import { Home, Compass, SquarePlay, User } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

export function BottomNav() {
    const pathname = usePathname();

    const navItems = [
        { label: "Home", icon: Home, href: "/" },
        { label: "Discover", icon: Compass, href: "/discover" },
        { label: "Library", icon: SquarePlay, href: "/library" }, // SquarePlay matches "Watchlist" or "Shorts" feel
        { label: "Profile", icon: User, href: "/profile" },
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-50 bg-black/95 backdrop-blur-md border-t border-white/10 pb-safe-area-bottom">
            <div className="flex justify-around items-center h-16">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={clsx(
                                "flex flex-col items-center justify-center w-full h-full space-y-1",
                                isActive ? "text-white" : "text-gray-500 hover:text-gray-300"
                            )}
                        >
                            <item.icon
                                className={clsx(
                                    "w-6 h-6 transition-transform",
                                    isActive && "scale-110"
                                )}
                                strokeWidth={isActive ? 2.5 : 2}
                            />
                            <span className="text-[10px] font-medium">{item.label}</span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}

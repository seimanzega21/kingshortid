"use client";

import { BottomNav } from "./BottomNav";

interface MobileLayoutProps {
    children: React.ReactNode;
    showNav?: boolean;
}

export function MobileLayout({ children, showNav = true }: MobileLayoutProps) {
    return (
        <div className="flex flex-col min-h-screen bg-black text-white max-w-md mx-auto relative overflow-hidden shadow-2xl">
            <main className="flex-1 overflow-y-auto pb-16 scrollbar-hide">
                {children}
            </main>
            {showNav && <BottomNav />}
        </div>
    );
}

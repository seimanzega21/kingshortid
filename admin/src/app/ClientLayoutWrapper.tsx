"use client";

import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "sonner";
import { useState, useEffect, useRef } from "react";
import { Menu, X, Film } from "lucide-react";

export default function ClientLayoutWrapper({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const router = useRouter();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isAuthorized, setIsAuthorized] = useState(false);

    // Touch gesture tracking for pulling sidebar in/out
    const touchStartX = useRef<number | null>(null);
    const touchStartY = useRef<number | null>(null);
    const touchCurrentX = useRef<number | null>(null);

    // Define full-screen auth routes that should NOT have a sidebar
    const authRoutes = ["/register", "/forgot-password", "/login"];
    const isAuthPage = authRoutes.includes(pathname);

    useEffect(() => {
        // Auth Check
        const checkAuth = () => {
            const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

            if (!token && !isAuthPage) {
                // Not logged in, trying to access protected page
                router.push('/login');
            } else if (token && isAuthPage) {
                // Logged in, trying to access login/register
                router.push('/');
            } else {
                setIsAuthorized(true);
            }
        };

        checkAuth();

        // Close sidebar on route change
        setSidebarOpen(false);
    }, [pathname, isAuthPage, router]);

    // Touch handlers for swipe to open/close sidebar on mobile
    const handleTouchStart = (e: React.TouchEvent) => {
        const touch = e.touches[0];
        touchStartX.current = touch.clientX;
        touchStartY.current = touch.clientY;
        touchCurrentX.current = touch.clientX;
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        if (touchStartX.current === null) return;
        const touch = e.touches[0];
        touchCurrentX.current = touch.clientX;
    };

    const handleTouchEnd = (e: React.TouchEvent) => {
        if (touchStartX.current === null || touchCurrentX.current === null) return;

        const deltaX = touchCurrentX.current - touchStartX.current;
        const deltaY = (touchStartY.current !== null && e.changedTouches[0])
            ? Math.abs(e.changedTouches[0].clientY - touchStartY.current)
            : 0;

        // Ensure swipe is predominantly horizontal (not vertical scroll)
        if (deltaY < Math.abs(deltaX) * 1.5) {
            // Swipe right from left edge (within 40px of screen edge) -> Open sidebar
            if (!sidebarOpen && touchStartX.current < 45 && deltaX > 50) {
                setSidebarOpen(true);
            }
            // Swipe left anywhere when sidebar is open -> Close sidebar
            else if (sidebarOpen && deltaX < -50) {
                setSidebarOpen(false);
            }
        }

        touchStartX.current = null;
        touchStartY.current = null;
        touchCurrentX.current = null;
    };

    // Prevent hydration mismatch or flash of protected content
    if (!isAuthorized && !isAuthPage && typeof window !== 'undefined' && !localStorage.getItem('token')) {
        return null; // or a loading spinner
    }

    if (isAuthPage) {
        return (
            <main className="min-h-screen bg-[#09090b]">
                {children}
                <Toaster richColors position="top-center" theme="dark" />
            </main>
        );
    }

    return (
        <div
            className="min-h-screen bg-[#09090b] flex flex-col md:flex-row relative"
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
        >
            {/* Mobile Header Bar - Fixed at top on mobile */}
            <header className="sticky top-0 z-30 flex md:hidden items-center justify-between h-14 px-4 bg-black/90 backdrop-blur-md border-b border-zinc-800 w-full">
                <button
                    onClick={() => setSidebarOpen(true)}
                    className="p-2 -ml-1 text-zinc-300 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors focus:outline-none"
                    aria-label="Buka Menu"
                >
                    <Menu size={22} />
                </button>
                <div className="flex items-center gap-2 font-bold text-lg text-yellow-500">
                    <Film className="h-5 w-5" />
                    <span>KingShort</span>
                </div>
                <div className="w-8" /> {/* spacer to balance title */}
            </header>

            {/* Edge Swipe Hint Zone: subtle indicator on left edge for swiping */}
            {!sidebarOpen && (
                <div
                    className="fixed inset-y-0 left-0 w-4 z-20 md:hidden pointer-events-auto"
                    aria-hidden="true"
                />
            )}

            {/* Sidebar Container */}
            <div
                className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-out md:translate-x-0 md:sticky md:top-0 md:h-screen ${
                    sidebarOpen ? 'translate-x-0 shadow-2xl shadow-black/80' : '-translate-x-full'
                }`}
            >
                <Sidebar onClose={() => setSidebarOpen(false)} />
            </div>

            {/* Backdrop Overlay for mobile when sidebar is open */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/80 md:hidden backdrop-blur-sm transition-opacity duration-300"
                    onClick={() => setSidebarOpen(false)}
                    aria-label="Tutup Menu"
                />
            )}

            {/* Main Content Area */}
            <main className="flex-1 min-h-screen bg-[#09090b] w-full overflow-x-hidden">
                {children}
            </main>

            <Toaster richColors position="top-center" theme="dark" />
        </div>
    );
}

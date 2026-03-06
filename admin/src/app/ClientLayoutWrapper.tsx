"use client";

import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "sonner";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";

export default function ClientLayoutWrapper({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const router = useRouter();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isAuthorized, setIsAuthorized] = useState(false);

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
        <div className="flex min-h-screen bg-[#09090b]">
            {/* Mobile Menu Button */}
            <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="fixed top-4 right-4 z-50 p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white md:hidden hover:bg-zinc-800 transition-colors shadow-lg"
            >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar - Hidden on mobile unless toggled */}
            <div className={`fixed inset-y-0 left-0 z-40 transform transition-transform duration-300 ease-in-out md:translate-x-0 md:sticky md:top-0 md:h-screen ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}>
                <Sidebar />
            </div>

            {/* Overlay for mobile when sidebar is open */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-30 bg-black/80 md:hidden backdrop-blur-sm"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Main Content - No margin left on mobile default */}
            <main className="flex-1 min-h-screen bg-[#09090b] w-full">
                {children}
            </main>

            <Toaster richColors position="top-center" theme="dark" />
        </div>
    );
}

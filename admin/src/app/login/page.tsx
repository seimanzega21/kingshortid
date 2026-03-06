"use client";

import Link from "next/link";
import { User, Lock, Eye, EyeOff, Check, ArrowRight } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function LoginPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);

    // Form State
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            const res = await fetch("/api/admin/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.message || "Login failed");
            }

            // Success
            toast.success("Login Successful!", {
                description: "Welcome back to the control room."
            });

            // Store token
            if (typeof window !== "undefined") {
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
            }

            // Redirect
            router.push("/");

        } catch (error: any) {
            toast.error("Access Denied", {
                description: error.message
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen w-full bg-[#09090b]">
            {/* Left Column - Form */}
            <div className="w-full lg:w-1/2 p-8 md:p-16 flex flex-col justify-center">
                <div className="max-w-md mx-auto w-full space-y-8">

                    {/* Logo & Header */}
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-purple-500 mb-6">
                            <div className="h-8 w-8 rounded bg-purple-500 flex items-center justify-center">
                                <span className="text-white font-bold text-xl">✨</span>
                            </div>
                            <span className="font-bold text-xl text-white">Drama Short Admin</span>
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">Welcome Back</h1>
                        <p className="text-zinc-400">Please sign in to access your dashboard.</p>
                    </div>

                    {/* Form */}
                    <form className="space-y-5" onSubmit={handleLogin}>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-zinc-300">Email Address</label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                <input
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    type="email"
                                    placeholder="admin@dramashort.com"
                                    required
                                    className="w-full bg-[#18181b] border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-medium text-zinc-300">Password</label>
                                <Link href="/forgot-password" className="text-sm text-purple-500 hover:text-purple-400 hover:underline">
                                    Forgot Password?
                                </Link>
                            </div>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                <input
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    required
                                    className="w-full bg-[#18181b] border border-zinc-800 rounded-lg pl-10 pr-10 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-400"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 pt-2">
                            <div
                                className={`h-5 w-5 rounded border cursor-pointer flex items-center justify-center transition-colors ${rememberMe ? 'bg-purple-600 border-purple-600' : 'border-zinc-700 bg-[#18181b]'
                                    }`}
                                onClick={() => setRememberMe(!rememberMe)}
                            >
                                {rememberMe && <Check size={14} className="text-white" />}
                            </div>
                            <label className="text-sm text-zinc-400 cursor-pointer" onClick={() => setRememberMe(!rememberMe)}>
                                Remember me for 30 days
                            </label>
                        </div>

                        <button
                            disabled={isLoading}
                            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3.5 rounded-lg transition-colors shadow-lg shadow-purple-900/20 flex items-center justify-center gap-2 group disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <span>Sign In</span>
                                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>

                        <p className="text-center text-sm text-zinc-500 pt-4">
                            Don't have an account? <Link href="/register" className="text-purple-500 hover:text-purple-400 font-medium hover:underline">Create Account</Link>
                        </p>

                    </form>

                    <footer className="pt-20 border-t border-zinc-800/50">
                        <p className="text-xs text-zinc-600">© 2024 Drama Short Admin Panel. All rights reserved.</p>
                    </footer>
                </div>
            </div>

            {/* Right Column - Image & Branding */}
            <div className="hidden lg:flex w-1/2 bg-[#050505] relative overflow-hidden items-center justify-center">
                {/* Background effects */}
                <div className="absolute inset-0 bg-gradient-to-bl from-purple-900/20 to-transparent" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-purple-600/10 blur-[100px] rounded-full" />

                <div className="relative z-10 p-12 max-w-lg text-left space-y-8">

                    <div>
                        <h2 className="text-5xl font-extrabold text-white leading-tight mb-6">
                            Welcome to the <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">control room.</span>
                        </h2>
                        <p className="text-lg text-zinc-400 leading-relaxed">
                            Data-driven insights and powerful management tools for your content empire.
                        </p>
                    </div>

                    {/* Decorative Stats */}
                    <div className="grid grid-cols-2 gap-4 pt-8">
                        <div className="bg-zinc-900/50 backdrop-blur border border-zinc-800 p-4 rounded-xl">
                            <p className="text-zinc-500 text-xs uppercase font-bold mb-1">Total Views</p>
                            <p className="text-2xl font-bold text-white">2.4M+</p>
                        </div>
                        <div className="bg-zinc-900/50 backdrop-blur border border-zinc-800 p-4 rounded-xl">
                            <p className="text-zinc-500 text-xs uppercase font-bold mb-1">Active Users</p>
                            <p className="text-2xl font-bold text-white">85k</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

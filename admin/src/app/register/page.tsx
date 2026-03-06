"use client";

import Link from "next/link";
import { User, Mail, Lock, Eye, EyeOff, RotateCw, Check } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function RegisterPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [agreed, setAgreed] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        password: "",
        confirmPassword: ""
    });
    const [isLoading, setIsLoading] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!agreed) {
            toast.error("Please agree to the Terms and Privacy Policy");
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            toast.error("Passwords do not match");
            return;
        }

        setIsLoading(true);

        try {
            const res = await fetch("/api/admin/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: formData.name,
                    email: formData.email,
                    password: formData.password
                })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.message || "Registration failed");
            }

            // Success
            toast.success("Account created successfully!", {
                description: "Welcome to the team."
            });

            // Store token
            if (typeof window !== "undefined") {
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
            }

            // Redirect
            router.push("/");

        } catch (error: any) {
            toast.error(error.message);
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
                        <h1 className="text-3xl font-bold tracking-tight text-white">Create Admin Account</h1>
                        <p className="text-zinc-400">Register a new administrator for the Drama Short control panel.</p>
                    </div>

                    {/* Form */}
                    <form className="space-y-5" onSubmit={handleSubmit}>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-zinc-300">Full Name</label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                <input
                                    name="name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    type="text"
                                    placeholder="Enter full name"
                                    required
                                    className="w-full bg-[#18181b] border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-zinc-300">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                <input
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    type="email"
                                    placeholder="admin@dramashort.com"
                                    required
                                    className="w-full bg-[#18181b] border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-sm font-medium text-zinc-300">Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                    <input
                                        name="password"
                                        value={formData.password}
                                        onChange={handleChange}
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
                            <div className="space-y-1.5">
                                <label className="text-sm font-medium text-zinc-300">Confirm Password</label>
                                <div className="relative">
                                    <RotateCw className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                    <input
                                        name="confirmPassword"
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        type={showConfirmPassword ? "text" : "password"}
                                        placeholder="••••••••"
                                        required
                                        className="w-full bg-[#18181b] border border-zinc-800 rounded-lg pl-10 pr-10 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-400"
                                    >
                                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-start gap-3 pt-2">
                            <div
                                className={`mt-1 h-5 w-5 rounded border cursor-pointer flex items-center justify-center transition-colors ${agreed ? 'bg-purple-600 border-purple-600' : 'border-zinc-700 bg-[#18181b]'
                                    }`}
                                onClick={() => setAgreed(!agreed)}
                            >
                                {agreed && <Check size={14} className="text-white" />}
                            </div>
                            <label className="text-sm text-zinc-400 leading-relaxed cursor-pointer" onClick={() => setAgreed(!agreed)}>
                                I agree to the <Link href="#" className="text-purple-500 hover:text-purple-400 hover:underline">Terms of Service</Link> and <Link href="#" className="text-purple-500 hover:text-purple-400 hover:underline">Privacy Policy</Link>.
                            </label>
                        </div>

                        <button
                            disabled={isLoading}
                            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3.5 rounded-lg transition-colors shadow-lg shadow-purple-900/20 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center"
                        >
                            {isLoading ? (
                                <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                "Create Account"
                            )}
                        </button>

                        <p className="text-center text-sm text-zinc-500 pt-4">
                            Already have an account? <Link href="/login" className="text-purple-500 hover:text-purple-400 font-medium hover:underline">Log In</Link>
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
                <div className="absolute inset-0 bg-gradient-to-tr from-purple-900/20 to-transparent" />

                <div className="relative z-10 p-12 max-w-lg text-center space-y-8">
                    <div className="rounded-full bg-zinc-900/50 border border-zinc-800 p-3 mx-auto w-fit backdrop-blur-sm">
                        <div className="flex items-center gap-2 text-green-500 px-3 py-1">
                            <div className="h-2 w-2 rounded-full bg-green-500" />
                            <span className="text-xs font-semibold uppercase tracking-wider">System Status: Operational</span>
                        </div>
                    </div>

                    <div>
                        <h2 className="text-5xl font-extrabold text-white leading-tight mb-6">
                            Manage your content like a <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">director.</span>
                        </h2>
                        <p className="text-lg text-zinc-400 leading-relaxed">
                            Access the full suite of tools to upload, manage, and analyze your drama shorts across all platforms.
                        </p>
                    </div>

                    <div className="flex items-center justify-center gap-4 pt-8">
                        <div className="flex -space-x-3">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-10 w-10 rounded-full border-2 border-black bg-zinc-800 overflow-hidden">
                                    { /* Placeholder avatars */}
                                    <div className="h-full w-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center text-[10px] text-white">Avatar</div>
                                </div>
                            ))}
                        </div>
                        <span className="text-sm font-medium text-white">Joined by 200+ creators</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

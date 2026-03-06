import Link from "next/link";
import { ChevronLeft, Mail, Lock, Play } from "lucide-react";

export default function LoginPage() {
    return (
        <div className="min-h-screen bg-black text-white flex flex-col px-6 py-8">
            {/* Header */}
            <div className="flex items-center mb-10">
                <Link href="/welcome" className="p-2 -ml-2 text-gray-400 hover:text-white">
                    <ChevronLeft size={28} />
                </Link>
            </div>

            {/* Title */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-yellow-500 mb-2">Selamat Datang</h1>
                <p className="text-gray-400">Masuk untuk melanjutkan menonton.</p>
            </div>

            {/* Form */}
            <form className="space-y-6">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300 ml-1">Email / No. HP</label>
                    <div className="relative">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            <Mail size={20} />
                        </div>
                        <input
                            type="email"
                            placeholder="Masukkan email anda"
                            className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300 ml-1">Password</label>
                    <div className="relative">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            <Lock size={20} />
                        </div>
                        <input
                            type="password"
                            placeholder="Masukkan password"
                            className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div className="flex justify-end">
                    <Link href="#" className="text-sm text-yellow-500 hover:text-yellow-400">
                        Lupa Password?
                    </Link>
                </div>

                <button className="w-full py-4 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full font-bold text-black text-lg hover:shadow-[0_0_20px_rgba(255,215,0,0.2)] transition-all">
                    Masuk
                </button>
            </form>

            {/* Divider */}
            <div className="my-8 flex items-center gap-4">
                <div className="h-[1px] bg-zinc-800 flex-1" />
                <span className="text-xs text-gray-500 uppercase">Atau masuk dengan</span>
                <div className="h-[1px] bg-zinc-800 flex-1" />
            </div>

            {/* Social Login */}
            <div className="grid grid-cols-2 gap-4">
                <button className="flex items-center justify-center gap-2 py-3 bg-zinc-900 rounded-xl border border-zinc-800 hover:bg-zinc-800 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-white flex items-center justify-center">
                        <span className="font-bold text-black text-xs">G</span>
                    </div>
                    <span className="font-medium text-sm">Google</span>
                </button>
                <button className="flex items-center justify-center gap-2 py-3 bg-zinc-900 rounded-xl border border-zinc-800 hover:bg-zinc-800 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-white">
                        <span className="font-bold text-xs">f</span>
                    </div>
                    <span className="font-medium text-sm">Facebook</span>
                </button>
            </div>

            {/* Footer */}
            <div className="mt-auto pt-8 flex justify-center">
                <p className="text-gray-400 text-sm">
                    Belum punya akun?{" "}
                    <Link href="/register" className="text-yellow-500 font-bold hover:underline">
                        Daftar
                    </Link>
                </p>
            </div>
        </div>
    );
}

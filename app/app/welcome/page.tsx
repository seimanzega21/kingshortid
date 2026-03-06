import Link from "next/link";
import { Play, ArrowRight } from "lucide-react";
import Image from "next/image";

export default function WelcomePage() {
    return (
        <div className="relative min-h-screen flex flex-col items-center px-6 pt-20 pb-12 bg-black text-white overflow-hidden font-sans">

            {/* Background Glow */}
            <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[120%] h-[50%] bg-blue-900/20 blur-[100px] rounded-full pointer-events-none" />

            {/* Logo Area */}
            <div className="relative z-10 flex flex-col items-center space-y-4 mb-12">
                <div className="w-24 h-24 bg-gradient-to-br from-yellow-500 to-yellow-700 rounded-3xl flex items-center justify-center shadow-[0_0_40px_rgba(255,215,0,0.3)] rotate-3">
                    <Play className="fill-black text-black w-10 h-10 ml-1" />
                </div>
                <h2 className="text-sm font-bold tracking-widest text-gray-400 uppercase">King Shortid</h2>
            </div>

            {/* Main Content */}
            <div className="relative z-10 flex flex-col items-center text-center space-y-6 flex-1 justify-center">

                <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight">
                    King <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-yellow-500 to-yellow-600">
                        Shortid
                    </span>
                </h1>

                <p className="text-gray-400 text-sm sm:text-base max-w-xs leading-relaxed">
                    Experience the next generation of storytelling. 1-minute episodes, endless emotions.
                </p>

                {/* 3 Posters Grid */}
                <div className="flex justify-center gap-4 py-8">
                    <div className="w-20 h-28 rounded-xl overflow-hidden -rotate-6 transform translate-y-2 border-2 border-zinc-800 bg-zinc-900 shadow-xl">
                        <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1549416866-996ac65440cb?q=80&w=2675&auto=format&fit=crop')] bg-cover bg-center" />
                    </div>
                    <div className="w-24 h-32 rounded-xl overflow-hidden z-20 border-2 border-yellow-500/50 shadow-2xl shadow-yellow-500/20 bg-zinc-900">
                        <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=2564&auto=format&fit=crop')] bg-cover bg-center" />
                    </div>
                    <div className="w-20 h-28 rounded-xl overflow-hidden rotate-6 transform translate-y-2 border-2 border-zinc-800 bg-zinc-900 shadow-xl">
                        <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1517849845537-4d257902454a?q=80&w=2535&auto=format&fit=crop')] bg-cover bg-center" />
                    </div>
                </div>
            </div>

            {/* Bottom Actions */}
            <div className="relative z-10 w-full max-w-sm space-y-6 mt-auto">

                <Link
                    href="/login"
                    className="group flex items-center justify-center w-full py-4 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full font-bold text-black text-lg transition-all hover:brightness-110 hover:shadow-[0_0_20px_rgba(255,215,0,0.4)]"
                >
                    Get Started
                    <ArrowRight className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" />
                </Link>

                <div className="text-center">
                    <p className="text-gray-400 text-sm">
                        Already have an account?{" "}
                        <Link href="/login" className="text-white font-bold underline decoration-yellow-500 decoration-2 underline-offset-4 hover:text-yellow-400 transition-colors">
                            Sign In
                        </Link>
                    </p>
                </div>

                <div className="flex justify-center gap-6 text-[10px] text-gray-600 uppercase tracking-wider font-medium">
                    <Link href="#" className="hover:text-gray-400">Privacy Policy</Link>
                    <span>•</span>
                    <Link href="#" className="hover:text-gray-400">Terms of Service</Link>
                </div>

            </div>
        </div>
    );
}

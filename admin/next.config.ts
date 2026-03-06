import type { NextConfig } from "next";

// All data API routes are proxied to VPS Supabase backend
// Local-only routes: /api/dashboard, /api/health, /api/admin/auth/*, /api/scraper/*, /api/uploads/*
const VPS_API = 'https://api.shortlovers.id';

const nextConfig: NextConfig = {
  turbopack: {},

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'stream.shortlovers.id',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'pub-8becf1ee9a914fc3a6525e2b50f11d04.r2.dev',
        pathname: '/**',
      },
    ],
  },

  typescript: {
    ignoreBuildErrors: true,
  },

  // Proxy data API routes to VPS Supabase backend (replaces D1/Cloudflare Workers)
  async rewrites() {
    return {
      beforeFiles: [
        // Drama & Episode CRUD
        { source: '/api/dramas/:path*', destination: `${VPS_API}/api/dramas/:path*` },
        { source: '/api/episodes/:path*', destination: `${VPS_API}/api/episodes/:path*` },
        // Categories
        { source: '/api/categories/:path*', destination: `${VPS_API}/api/categories/:path*` },
        // Settings
        { source: '/api/settings/:path*', destination: `${VPS_API}/api/settings/:path*` },
        { source: '/api/settings', destination: `${VPS_API}/api/settings` },
        // Auth (guest, google, facebook, login, register, me)
        { source: '/api/auth/:path*', destination: `${VPS_API}/api/auth/:path*` },
        // User data (history, watchlist, favorites, collection)
        { source: '/api/user/:path*', destination: `${VPS_API}/api/user/:path*` },
        // Rewards
        { source: '/api/rewards/:path*', destination: `${VPS_API}/api/rewards/:path*` },
        // Admin data endpoints (users list, user detail, dashboard stats)
        // NOTE: /api/admin/auth/* is NOT proxied — handled locally by Next.js for admin panel login
        { source: '/api/admin/dashboard', destination: `${VPS_API}/api/admin/dashboard` },
        { source: '/api/admin/users/:path*', destination: `${VPS_API}/api/admin/users/:path*` },
        { source: '/api/admin/users', destination: `${VPS_API}/api/admin/users` },
        // Admin panel pages call /api/users — map to VPS /api/admin/users
        { source: '/api/users/bulk-delete', destination: `${VPS_API}/api/admin/users/bulk-delete` },
        { source: '/api/users/:id', destination: `${VPS_API}/api/admin/users/:id` },
        { source: '/api/users', destination: `${VPS_API}/api/admin/users` },
        // Notifications
        { source: '/api/notifications/:path*', destination: `${VPS_API}/api/notifications/:path*` },
      ],
      afterFiles: [
        {
          source: '/uploads/:path*',
          destination: '/api/uploads/:path*',
        },
      ],
      fallback: [],
    };
  },

  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        util: false,
        crypto: false,
        stream: false,
        buffer: false,
      };
    }
    return config;
  },
};

export default nextConfig;

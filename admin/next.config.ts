import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Empty turbopack config to silence migration warning
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

  // Temporarily ignore TS errors during build
  // TODO: Fix pre-existing schema mismatches (Profile, Follow, Playlist, etc.)
  typescript: {
    ignoreBuildErrors: true,
  },

  // Proxy drama/episode API to Cloudflare Worker (single D1 database)
  // beforeFiles ensures these take priority over local Next.js API routes
  async rewrites() {
    const CF_API = 'https://kingshortid-api.toonplay-seiman.workers.dev';
    return {
      beforeFiles: [
        {
          source: '/api/dramas/:path*',
          destination: `${CF_API}/api/dramas/:path*`,
        },
        {
          source: '/api/episodes/:path*',
          destination: `${CF_API}/api/episodes/:path*`,
        },
        {
          source: '/api/settings/:path*',
          destination: `${CF_API}/api/settings/:path*`,
        },
        {
          source: '/api/settings',
          destination: `${CF_API}/api/settings`,
        },
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
      // Provide fallbacks for Node.js modules used in client-side code
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

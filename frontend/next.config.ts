import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'tokens.1inch.io',
        pathname: '/**',
      },
    ],
  },
  output: 'standalone',
};

export default nextConfig;

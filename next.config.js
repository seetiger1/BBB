/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable API routes to be treated as serverless functions
  experimental: {
    serverComponentsExternalPackages: [],
  },
};

module.exports = nextConfig;

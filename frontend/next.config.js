/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/jobs/:path*',
        destination: 'http://localhost:8000/api/jobs/:path*',
      },
      {
        source: '/api/comments/:path*',
        destination: 'http://localhost:8000/api/comments/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
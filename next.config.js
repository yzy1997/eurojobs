/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/jobs/:path*',
        destination: `${apiUrl}/api/jobs/:path*`,
      },
      {
        source: '/api/comments/:path*',
        destination: `${apiUrl}/api/comments/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
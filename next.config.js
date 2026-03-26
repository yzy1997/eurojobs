/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'https://eurojobs-production.up.railway.app').replace('http://', 'https://');
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
const rawBackendUrl =
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://127.0.0.1:8000';
const backendUrl = rawBackendUrl.replace(/\/+$/, '');

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/thumbs/:path*',
        destination: `${backendUrl}/thumbs/:path*`,
      },
      {
        source: '/photos/:path*',
        destination: `${backendUrl}/photos/:path*`,
      },
    ];
  },
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

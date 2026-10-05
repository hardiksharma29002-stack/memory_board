/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/thumbs/:path*',
        destination: 'http://localhost:8000/thumbs/:path*',
      },
      {
        source: '/photos/:path*',
        destination: 'http://localhost:8000/photos/:path*',
      },
    ];
  },
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

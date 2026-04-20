/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  basePath: process.env.NODE_ENV === 'production' ? '/vine' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/vine/' : '',
};

module.exports = nextConfig;

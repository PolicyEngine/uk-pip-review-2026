/** @type {import('next').NextConfig} */
// No basePath, rewrites or deploy target yet: nothing deploys from this
// repository (see .github/workflows/deploy.yml). Set basePath in
// src/lib/basePath.json and here together when the team picks a route.
import basePathConfig from "./src/lib/basePath.json" with { type: "json" };

const { basePath } = basePathConfig;

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@policyengine/ui-kit"],
  ...(basePath ? { basePath } : {}),
  // Pre-release: every response says noindex, as well as the robots meta in
  // app/layout.jsx. Remove both together at final sign-off, not before.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }],
      },
    ];
  },
};

export default nextConfig;

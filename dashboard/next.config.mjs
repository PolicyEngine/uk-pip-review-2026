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
};

export default nextConfig;

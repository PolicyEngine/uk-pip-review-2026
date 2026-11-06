import { PolicyEngineShell } from "@policyengine/ui-kit/layout";
import "@policyengine/ui-kit/styles.css";
import localFont from "next/font/local";
import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import { SITE_HEADER_STYLES, SITE_NAV_ITEMS } from "../src/utils/siteNav";

import "./globals.css";
// The PolicyEngine tokens, bundled with the page, after globals.css, as on
// the AB2026 dashboard.
import "@policyengine/ui-kit/legacy/tokens.css";
import "./siteHeader.css";

// Inter, committed with the page (fonts/: the variable face, Latin subset;
// SIL Open Font License in fonts/OFL.txt), as on the AB2026 dashboard: the
// build fetches nothing from Google.
const inter = localFont({
  src: "./fonts/inter-latin-variable.woff2",
  weight: "100 900",
  style: "normal",
  display: "swap",
  variable: "--font-inter",
  adjustFontFallback: "Arial",
});

// noindex until the figures are final and signed off. Check it in the built
// HTML (dashboard/scripts/smoke-built-site.sh), not only here.
export const metadata = {
  title: "PIP review: costs and who is affected | PolicyEngine",
  description:
    "Pre-release template. What the proposals of the independent review of Personal Independence Payment would cost and who they would affect, from PolicyEngine UK microsimulation.",
  robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en-GB" className={inter.variable}>
      <body>
        {/* The site header with policyengine.org's own menu, including the
            phone menu (src/utils/siteNav.js; siteHeader.css for its look) */}
        <PolicyEngineShell country="uk" showFooter={false} headerProps={{ navItems: SITE_NAV_ITEMS, styles: SITE_HEADER_STYLES }}>
          {children}
          <PolicyEngineFooter />
        </PolicyEngineShell>
      </body>
    </html>
  );
}

import localFont from "next/font/local";
import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import "./globals.css";

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
        <PolicyEngineHeader />
        {children}
        <PolicyEngineFooter />
      </body>
    </html>
  );
}

import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import "./globals.css";

// noindex until the figures are final and signed off. Check it in the built
// HTML and on the protected preview, not only here.
export const metadata = {
  title: "PIP review: costs and who is affected | PolicyEngine",
  description:
    "Pre-release template. What the proposals of the independent review of Personal Independence Payment would cost and who they would affect, from PolicyEngine UK microsimulation.",
  robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en-GB">
      <body>
        <PolicyEngineHeader />
        {children}
        <PolicyEngineFooter />
      </body>
    </html>
  );
}

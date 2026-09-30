import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  metadataBase: new URL("https://saltanatrestaurant.com"),
  title: { default: "Saltanat Restaurant Karachi | Dine-in Under the Stars", template: "%s | Saltanat Restaurant Karachi" },
  description: "Gather over Pakistani BBQ, karahi and family favourites at Saltanat Restaurant on Stadium Road, Karachi. Dine under the stars and request your table.",
  keywords: ["Saltanat Restaurant Karachi", "Stadium Road Karachi restaurant", "family restaurant Karachi", "BBQ and karahi in Karachi", "event booking Karachi"],
  openGraph: { title: "Saltanat Restaurant | Dine-in Under the Stars", description: "A lively family dining destination on Stadium Road, Karachi.", type: "website", images: ["/brand/banner-01.jpg"] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="site-shell">
            <SiteHeader />
            <main>{children}</main>
            <SiteFooter />
          </div>
        </Providers>
      </body>
    </html>
  );
}
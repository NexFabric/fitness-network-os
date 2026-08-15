import type { Metadata, Viewport } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#020617",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL("https://gymclubnex.com"),
  title: {
    default: "GymClubNex | Fitness Network OS",
    template: "%s | GymClubNex",
  },
  description:
    "Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi. Dinamik QR turnike erişimi, çok şubeli yönetim ve PostgreSQL RLS ile tam veri izolasyonu.",
  keywords: [
    "spor salonu yönetim sistemi",
    "fitness club software",
    "fitness network os",
    "dinamik qr turnike",
    "spor kulübü otomasyonu",
    "multi-tenant gym pos",
    "athletic ops console",
  ],
  authors: [{ name: "GymClubNex Team", url: "https://gymclubnex.com" }],
  creator: "GymClubNex",
  publisher: "GymClubNex",
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    title: "GymClubNex | Fitness Network OS",
    description:
      "Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi. Operasyonu bize bırakın, performansa odaklanın.",
    url: "https://gymclubnex.com",
    siteName: "GymClubNex",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "GymClubNex | Fitness Network OS",
      },
    ],
    locale: "tr_TR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "GymClubNex | Fitness Network OS",
    description:
      "Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi.",
    images: ["/og-image.jpg"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr" className={`${dmSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2.5 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-accent"
        >
          Ana içeriğe atla
        </a>
        <Header />
        <main id="main-content" tabIndex={-1} className="flex-1 pt-16 outline-none">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}

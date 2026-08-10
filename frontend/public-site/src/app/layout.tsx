import type { Metadata } from "next";
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

export const metadata: Metadata = {
  metadataBase: new URL("https://gymclubnex.com"),
  title: {
    default: "GymClubNex | Fitness Network OS",
    template: "%s | GymClubNex",
  },
  description:
    "Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi. Operasyonu bize bırakın, performansa odaklanın.",
  openGraph: {
    title: "GymClubNex | Fitness Network OS",
    description:
      "Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi.",
    url: "https://gymclubnex.com",
    siteName: "GymClubNex",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "GymClubNex Athletic Ops Console",
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
        <Header />
        <main className="flex-1 pt-16">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

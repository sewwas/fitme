import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://fitme.lk"),
  title: "FIT ME | Train with Purpose & Move with Confidence",
  description:
    "Fit Me is a premier athletic fitness facility in Pitigala offering structured coaching, heavy iron training, nutrition calibration, and measurable progression.",
  keywords: [
    "Fit Me",
    "Fitness Studio",
    "Pitigala",
    "Personal Training",
    "Strength Training",
    "Bodybuilding",
    "Athletic Performance",
    "Train with Purpose",
  ],
  icons: {
    icon: "/images/fitme-official-logo.jpg",
  },
  openGraph: {
    title: "FIT ME | Train with Purpose & Move with Confidence",
    description:
      "A premium, cinematic fitness destination. Move with confidence and build lasting physical discipline.",
    url: "https://fitme.lk",
    siteName: "FIT ME",
    images: [
      {
        url: "/images/fitme-official-cover.jpg",
        width: 1200,
        height: 630,
        alt: "Fit Me Premium Fitness Studio",
      },
    ],
    locale: "en_US",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} scroll-smooth`}
    >
      <body className="min-h-screen bg-[#0B0D0E] text-[#F8FAFC] antialiased selection:bg-[#76C043] selection:text-[#0B0D0E]">
        {children}
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import Script from "next/script";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { AssemblyProvider } from "@/contexts/AssemblyContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import ServiceWorkerInit from "@/components/ServiceWorkerInit";
import WebVitalsReporter from "@/components/WebVitalsReporter";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  preload: true,
  fallback: ["system-ui", "arial"],
});

export const viewport: Viewport = {
  themeColor: "#8B5CF6",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export const metadata: Metadata = {
  title: {
    default: "ViralPilot - AI Video Generator",
    template: "%s | ViralPilot",
  },
  description: "Create viral short-form videos on autopilot with AI. Automated content creation for TikTok, Instagram, and YouTube Shorts.",
  keywords: ["AI video generator", "viral videos", "TikTok", "Instagram Reels", "YouTube Shorts", "content creation", "automation"],
  authors: [{ name: "ViralPilot Team" }],
  creator: "ViralPilot",
  publisher: "ViralPilot",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://viralpilot.app'),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    siteName: "ViralPilot",
    title: "ViralPilot - AI Video Generator",
    description: "Create viral short-form videos on autopilot with AI",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "ViralPilot - AI Video Generator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ViralPilot - AI Video Generator",
    description: "Create viral short-form videos on autopilot with AI",
    images: ["/og-image.png"],
    creator: "@viralpilot",
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
  icons: {
    icon: [
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/icon-152.png", sizes: "152x152", type: "image/png" },
      { url: "/icon-180.png", sizes: "180x180", type: "image/png" },
    ],
  },
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "ViralPilot",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        variables: {
          colorPrimary: "#8B5CF6",
        },
      }}
    >
      <html lang="en" className="dark">
        <head>
          <link rel="preconnect" href="https://fonts.googleapis.com" />
          <link rel="dns-prefetch" href="https://oiynhonwhxgmmowqbdqb.supabase.co" />
        </head>
        <body className={inter.className}>
          <ErrorBoundary>
            <AssemblyProvider>
              {children}
              <Toaster />
              <ServiceWorkerInit />
              <WebVitalsReporter />
            </AssemblyProvider>
          </ErrorBoundary>

          {/* Analytics placeholder - replace with your analytics service */}
          {process.env.NEXT_PUBLIC_GA_ID && (
            <>
              <Script
                src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`}
                strategy="afterInteractive"
              />
              <Script id="google-analytics" strategy="afterInteractive">
                {`
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}');
                `}
              </Script>
            </>
          )}
        </body>
      </html>
    </ClerkProvider>
  );
}
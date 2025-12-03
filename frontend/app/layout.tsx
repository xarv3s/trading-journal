import type { Metadata } from "next";
// import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Navbar } from "@/components/shared/navbar";
import Providers from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";

// const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Trading Journal",
  description: "Advanced Trading Journal & Analytics",
};

import { ZerodhaAuthGuard } from "@/components/auth/zerodha-guard"

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <Providers>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <ZerodhaAuthGuard>
              <Navbar />
              <main className="container mx-auto py-6 px-4">
                {children}
              </main>
            </ZerodhaAuthGuard>
            <Toaster />
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  );
}

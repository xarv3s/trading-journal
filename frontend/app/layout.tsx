import type { Metadata } from "next";
// import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Sidebar } from "@/components/shared/sidebar";
import Providers from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import { ZerodhaAuthGuard } from "@/components/auth/zerodha-guard";

// const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Trading Platform",
  description: "Advanced Trading Journal & Analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased" suppressHydrationWarning>
        <Providers>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <ZerodhaAuthGuard>
              <div className="flex h-screen overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto bg-background p-6">
                  {children}
                </main>
              </div>
            </ZerodhaAuthGuard>
            <Toaster />
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  );
}

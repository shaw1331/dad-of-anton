import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";

const geist = Geist({ subsets: ["latin"] });
const geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Dad of Anton",
  description: "Workflow orchestration dashboard",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try{if(localStorage.theme==='dark'||(!localStorage.theme&&window.matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.classList.add('dark')}catch(e){}`,
          }}
        />
      </head>
      <body className={`${geist.className} antialiased`} suppressHydrationWarning>
        <ThemeProvider>
          <div className="min-h-screen transition-colors dark:bg-black">
            <nav className="border-b border-gray-200 bg-white transition-colors dark:border-[rgba(255,255,255,0.06)] dark:bg-[#0a0a0a]">
              <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                <Link href="/" className="flex items-center gap-2">
                  <svg
                    className="h-7 w-7 text-gray-900 dark:text-[#EDEDED]"
                    viewBox="0 0 32 32"
                    fill="currentColor"
                    suppressHydrationWarning
                  >
                    <ellipse cx="12" cy="14" rx="5" ry="6" fill="none" stroke="currentColor" strokeWidth="1.5"/>
                    <ellipse cx="12" cy="14" rx="3" ry="5" fill="none" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M8 10c-1-3 0-6 2-7" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <path d="M7 14c-3 0-5-1-5 1s2 2 4 2" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <circle cx="10" cy="12" r="1" fill="currentColor"/>
                    <path d="M15 20v4M9 20v4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  <span className="text-lg font-bold text-gray-900 dark:text-[#EDEDED]">
                    Dad of Anton
                  </span>
                </Link>
                <div className="flex items-center gap-1">
                  <Link
                    href="/"
                    className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-[#888888] dark:hover:bg-[#111111] dark:hover:text-[#EDEDED]"
                  >
                    Home
                  </Link>
                  <Link
                    href="/home"
                    className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-[#888888] dark:hover:bg-[#111111] dark:hover:text-[#EDEDED]"
                  >
                    Workflows
                  </Link>
                  <Link
                    href="/stocks"
                    className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-[#888888] dark:hover:bg-[#111111] dark:hover:text-[#EDEDED]"
                  >
                    Stocks
                  </Link>
                  <Link
                    href="/screener"
                    className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-[#888888] dark:hover:bg-[#111111] dark:hover:text-[#EDEDED]"
                  >
                    NSE Screener
                  </Link>
                  <Link
                    href="/tradingview"
                    className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-[#888888] dark:hover:bg-[#111111] dark:hover:text-[#EDEDED]"
                  >
                    TradingView
                  </Link>
                  <div className="ml-2">
                    <ThemeToggle />
                  </div>
                </div>
              </div>
            </nav>
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}

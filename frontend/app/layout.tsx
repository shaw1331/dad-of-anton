import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { Sparkles, LayoutDashboard, Home } from "lucide-react";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Separator } from "@/components/ui/separator";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Dad of Anton",
  description: "Workflow orchestration dashboard",
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
      <body className={`${inter.className}`} suppressHydrationWarning>
        <ThemeProvider>
          <div className="min-h-screen bg-background transition-colors">
            <nav className="border-b border-border bg-card transition-colors">
              <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                <Link href="/" className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                    <Sparkles className="h-4 w-4 text-primary-foreground" />
                  </div>
                  <span className="text-lg font-bold text-foreground">
                    Dad of Anton
                  </span>
                </Link>
                <div className="flex items-center gap-1">
                  <Link
                    href="/"
                    className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                  >
                    <Home className="h-4 w-4" />
                    Home
                  </Link>
                  <Link
                    href="/workflows"
                    className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    Workflows
                  </Link>
                  <Separator orientation="vertical" className="mx-1 h-6" />
                  <ThemeToggle />
                </div>
              </div>
            </nav>
            <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}

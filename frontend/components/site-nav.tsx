"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";

const LINKS = [
  { href: "/trades", label: "Trades" },
  { href: "/workflows", label: "Workflows" },
  { href: "/screener", label: "NSE Screener" },
  { href: "/groww-news", label: "Groww News" },
  { href: "/trendlyne", label: "Trendlyne" },
  { href: "/tradingview", label: "TradingView" },
  { href: "/stock-jury", label: "Stock Jury" },
  { href: "/evaluation", label: "Evaluation" },
] as const;

export function SiteNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  function linkClass(href: string, stacked = false) {
    const active = pathname === href || pathname.startsWith(`${href}/`);
    return [
      stacked ? "block rounded-lg px-3 py-2.5 text-sm font-medium" : "rounded-lg px-3 py-2 text-sm font-medium",
      active
        ? "bg-accent text-accent-foreground"
        : "text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
    ].join(" ");
  }

  return (
    <nav className="border-b border-border bg-card transition-colors">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-2 px-4 sm:h-16 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-2" onClick={() => setOpen(false)}>
          <svg
            className="h-6 w-6 shrink-0 text-foreground"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"
            />
          </svg>
          <span className="truncate text-base font-bold text-foreground sm:text-lg">
            Dad of Anton
          </span>
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className={linkClass(link.href)}>
              {link.label}
            </Link>
          ))}
          <div className="ml-2">
            <ThemeToggle />
          </div>
        </div>

        <div className="flex items-center lg:hidden">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {open ? (
        <div className="space-y-1 border-t border-border px-4 py-2 lg:hidden">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={linkClass(link.href, true)}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>
      ) : null}
    </nav>
  );
}

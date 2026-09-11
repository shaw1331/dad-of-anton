"use client";

import { useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  CandlestickChart,
  Landmark,
  TrendingUp,
  Wallet,
} from "lucide-react";
import {
  summarizeTrades,
  tradeCapital,
  tradeMark,
  tradePnl,
  tradePnlPct,
  type Trade,
  type TradeStatus,
} from "@/lib/api/trades";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type StatusFilter = "all" | TradeStatus;
type SortKey =
  | "ticker"
  | "openedAt"
  | "capital"
  | "pnl"
  | "entryPrice"
  | "quantity";

function formatInr(value: number, digits = 0): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function formatPrice(value: number | null): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatSignedInr(value: number): string {
  const abs = formatInr(Math.abs(value));
  if (value > 0) return `+${abs}`;
  if (value < 0) return `-${abs}`;
  return abs;
}

function pnlClass(value: number | null): string {
  if (value == null || value === 0) return "text-muted-foreground";
  return value > 0
    ? "text-emerald-600 dark:text-emerald-400"
    : "text-red-600 dark:text-red-400";
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function OutcomeBadge({ trade }: { trade: Trade }) {
  if (trade.status === "open") {
    return <Badge variant="info">Open</Badge>;
  }
  if (trade.closeReason === "tp") {
    return (
      <Badge variant="success" title="Take Profit">
        TP
      </Badge>
    );
  }
  if (trade.closeReason === "sl") {
    return (
      <Badge variant="destructive" title="Stop Loss">
        SL
      </Badge>
    );
  }
  return <Badge variant="warning">Manual</Badge>;
}

function sortValue(trade: Trade, col: SortKey): string | number {
  switch (col) {
    case "ticker":
      return trade.ticker;
    case "openedAt":
      return Date.parse(trade.openedAt) || 0;
    case "capital":
      return tradeCapital(trade);
    case "pnl":
      return tradePnl(trade) ?? 0;
    case "entryPrice":
      return trade.entryPrice;
    case "quantity":
      return trade.quantity;
  }
}

function SortIcon({
  active,
  asc,
}: {
  active: boolean;
  asc: boolean;
}) {
  if (!active) return <ArrowUpDown className="h-3 w-3 opacity-30" />;
  return asc ? (
    <ArrowUp className="h-3 w-3 text-primary" />
  ) : (
    <ArrowDown className="h-3 w-3 text-primary" />
  );
}

export function TradesView({ trades }: { trades: Trade[] }) {
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [sortCol, setSortCol] = useState<SortKey>("openedAt");
  const [sortAsc, setSortAsc] = useState(false);

  const summary = useMemo(() => summarizeTrades(trades), [trades]);

  const visible = useMemo(() => {
    const rows =
      filter === "all" ? trades.slice() : trades.filter((t) => t.status === filter);

    rows.sort((a, b) => {
      const av = sortValue(a, sortCol);
      const bv = sortValue(b, sortCol);
      const primary =
        typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av).localeCompare(String(bv));
      if (primary !== 0) return sortAsc ? primary : -primary;
      return (Date.parse(b.openedAt) || 0) - (Date.parse(a.openedAt) || 0);
    });
    return rows;
  }, [trades, filter, sortCol, sortAsc]);

  function handleSort(col: SortKey) {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(col === "ticker");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Trades
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Past and open positions with running P&amp;L, capital deployed, and
          whether closed trades hit take-profit, stop-loss, or were exited
          manually.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">
                Running P&amp;L
              </p>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className={`text-2xl font-semibold tabular-nums ${pnlClass(summary.runningPnl)}`}>
              {formatSignedInr(summary.runningPnl)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Unrealized P&amp;L
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">
                Capital deployed
              </p>
              <Wallet className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-semibold tabular-nums text-foreground">
              {formatInr(summary.capitalDeployed)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Entry value of open positions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">
                Realized P&amp;L
              </p>
              <Landmark className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className={`text-2xl font-semibold tabular-nums ${pnlClass(summary.realizedPnl)}`}>
              {formatSignedInr(summary.realizedPnl)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {summary.winCount} win{summary.winCount === 1 ? "" : "s"} ·{" "}
              {summary.lossCount} loss{summary.lossCount === 1 ? "" : "es"} ·
              total {formatSignedInr(summary.totalPnl)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">
                Closed outcomes
              </p>
              <CandlestickChart className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-semibold tabular-nums text-foreground">
              {summary.closedCount}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {summary.closedBy.tp} TP · {summary.closedBy.sl} SL ·{" "}
              {summary.closedBy.manual} manual
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {(["all", "open", "closed"] as const).map((value) => (
          <Button
            key={value}
            size="sm"
            variant={filter === value ? "default" : "outline"}
            onClick={() => setFilter(value)}
          >
            {value === "all" ? "All" : value === "open" ? "Open" : "Closed"}
            <Badge
              variant={filter === value ? "secondary" : "muted"}
              className="ml-1"
            >
              {value === "all"
                ? trades.length
                : trades.filter((t) => t.status === value).length}
            </Badge>
          </Button>
        ))}
      </div>

      {visible.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <CandlestickChart className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No trades match this filter.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full table-fixed text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                {(
                  [
                    ["ticker", "Ticker"],
                    ["openedAt", "Opened"],
                    [null, "Side"],
                    ["quantity", "Qty"],
                    ["entryPrice", "Entry"],
                    [null, "SL"],
                    [null, "TP"],
                    [null, "Mark"],
                    ["capital", "Capital"],
                    ["pnl", "P&L"],
                    [null, "Outcome"],
                    [null, "Closed"],
                  ] as [SortKey | null, string][]
                ).map(([key, label]) => (
                  <th key={label} className="px-2 py-2.5 first:pl-4 last:pr-4">
                    {key ? (
                      <button
                        type="button"
                        onClick={() => handleSort(key)}
                        className="inline-flex items-center gap-1 font-medium text-muted-foreground transition-colors hover:text-foreground"
                      >
                        {label}
                        <SortIcon
                          active={sortCol === key}
                          asc={sortAsc}
                        />
                      </button>
                    ) : (
                      <span className="font-medium text-muted-foreground">
                        {label}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((trade) => {
                const pnl = tradePnl(trade);
                const pct = tradePnlPct(trade);
                return (
                  <tr
                    key={trade.id}
                    title={trade.notes ?? undefined}
                    className="border-b border-border/50 transition-colors hover:bg-muted/50"
                  >
                    <td className="px-2 py-2 first:pl-4">
                      <p className="truncate font-medium text-foreground">
                        {trade.ticker}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {trade.name}
                      </p>
                    </td>
                    <td className="px-2 py-2 text-muted-foreground">
                      {formatDate(trade.openedAt)}
                    </td>
                    <td className="px-2 py-2">
                      <Badge
                        variant={trade.side === "long" ? "success" : "destructive"}
                      >
                        {trade.side === "long" ? "Long" : "Short"}
                      </Badge>
                    </td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">
                      {trade.quantity.toLocaleString("en-IN")}
                    </td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">
                      {formatPrice(trade.entryPrice)}
                    </td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">
                      {formatPrice(trade.stopLoss)}
                    </td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">
                      {formatPrice(trade.takeProfit)}
                    </td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">
                      {formatPrice(tradeMark(trade))}
                    </td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">
                      {formatInr(tradeCapital(trade))}
                    </td>
                    <td
                      className={`px-2 py-2 tabular-nums font-medium ${pnlClass(pnl)}`}
                    >
                      {pnl == null ? "—" : formatSignedInr(pnl)}
                      {pct != null && (
                        <span className="ml-1 text-xs font-normal">
                          ({pct > 0 ? "+" : ""}
                          {pct.toFixed(1)}%)
                        </span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      <OutcomeBadge trade={trade} />
                    </td>
                    <td className="px-2 py-2 last:pr-4 text-muted-foreground">
                      {trade.status === "closed"
                        ? formatDate(trade.closedAt)
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

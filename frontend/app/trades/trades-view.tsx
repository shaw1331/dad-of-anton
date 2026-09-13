"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  CandlestickChart,
  Landmark,
  LogOut,
  Loader2,
  Pencil,
  Plus,
  StickyNote,
  Trash2,
  TrendingUp,
  Wallet,
  XCircle,
} from "lucide-react";
import {
  summarizeTrades,
  tradeCapital,
  tradeMark,
  tradePnl,
  tradePnlPct,
  getTrades,
  getTradeQuote,
  createTrade,
  closeTrade,
  updateTrade,
  deleteTrade,
  type Trade,
  type TradeStatus,
  type TradeQuote,
} from "@/lib/api/trades";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TickerInput } from "@/components/ticker-input";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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

function formatDayMonth(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
  });
}

function TradeActions({
  trade,
  onEdit,
  onClose,
  onDelete,
}: {
  trade: Trade;
  onEdit: (trade: Trade) => void;
  onClose: (trade: Trade) => void;
  onDelete: (trade: Trade) => void;
}) {
  const canClose = trade.status === "open" && trade.currentPrice != null;
  return (
    <div className="inline-flex items-center rounded-md border border-border/60 p-0.5">
      <Button
        size="sm"
        variant="ghost"
        title="Edit"
        className="h-7 w-7 p-0 text-muted-foreground"
        onClick={() => onEdit(trade)}
      >
        <Pencil className="h-3.5 w-3.5" />
      </Button>
      {canClose ? (
        <Button
          size="sm"
          variant="ghost"
          title="Close position"
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
          onClick={() => onClose(trade)}
        >
          <LogOut className="h-3.5 w-3.5" />
        </Button>
      ) : null}
      <Button
        size="sm"
        variant="ghost"
        title="Delete"
        className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
        onClick={() => onDelete(trade)}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
      {trade.notes ? (
        <span
          title={trade.notes}
          className="inline-flex h-7 w-7 items-center justify-center text-muted-foreground"
        >
          <StickyNote className="h-3.5 w-3.5" />
        </span>
      ) : null}
    </div>
  );
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

export function TradesView() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [sortCol, setSortCol] = useState<SortKey>("openedAt");
  const [sortAsc, setSortAsc] = useState(false);

  // Add form state
  const [addTicker, setAddTicker] = useState("");
  const [quoteTicker, setQuoteTicker] = useState("");
  const [quote, setQuote] = useState<TradeQuote | null>(null);
  const [addQty, setAddQty] = useState("");
  const [addSl, setAddSl] = useState("");
  const [addTp, setAddTp] = useState("");
  const [addNotes, setAddNotes] = useState("");
  const [quoting, setQuoting] = useState(false);
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const [closeTrade_, setCloseTrade] = useState<Trade | null>(null);
  const [deleteTrade_, setDeleteTrade] = useState<Trade | null>(null);
  const [editTrade, setEditTrade] = useState<Trade | null>(null);
  const [editQty, setEditQty] = useState("");
  const [editSl, setEditSl] = useState("");
  const [editTp, setEditTp] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editError, setEditError] = useState<string | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);

  const fetchTrades = useCallback(async () => {
    try {
      const data = await getTrades();
      setTrades(data);
    } catch (err: any) {
      setError(err.message || "Failed to load trades");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrades();
  }, [fetchTrades]);

  useEffect(() => {
    if (!quoteTicker) {
      setQuote(null);
      setQuoting(false);
      return;
    }
    let cancelled = false;
    setQuoting(true);
    setAddError(null);
    getTradeQuote(quoteTicker)
      .then((q) => {
        if (cancelled) return;
        setQuote(q);
        setAddQty(String(q.quantity));
        setAddSl(String(q.stopLoss));
        setAddTp(String(q.takeProfit));
      })
      .catch((err) => {
        if (cancelled) return;
        setQuote(null);
        setAddError(err.message || "Quote failed");
      })
      .finally(() => {
        if (!cancelled) setQuoting(false);
      });
    return () => { cancelled = true; };
  }, [quoteTicker]);

  async function handleAdd() {
    if (!addTicker || !quote) return;
    setAdding(true);
    setAddError(null);
    try {
      const created = await createTrade({
        ticker: addTicker,
        quantity: Number(addQty),
        stopLoss: Number(addSl),
        takeProfit: Number(addTp),
        notes: addNotes || undefined,
      });
      setTrades((prev) => [created, ...prev.filter((t) => t.id !== created.id)]);
      setAddTicker("");
      setQuoteTicker("");
      setQuote(null);
      setAddQty("");
      setAddSl("");
      setAddTp("");
      setAddNotes("");
    } catch (err: any) {
      setAddError(err.message || "Create failed");
    } finally {
      setAdding(false);
    }
  }

  async function handleClose() {
    if (!closeTrade_ || closeTrade_.currentPrice == null) return;
    try {
      const updated = await closeTrade(closeTrade_.id, {
        reason: "manual",
        exitPrice: closeTrade_.currentPrice,
      });
      setTrades((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      setCloseTrade(null);
    } catch (err: any) {
      setError(err.message || "Close failed");
    }
  }

  async function handleDelete() {
    if (!deleteTrade_) return;
    try {
      const id = deleteTrade_.id;
      await deleteTrade(id);
      setTrades((prev) => prev.filter((t) => t.id !== id));
      setDeleteTrade(null);
    } catch (err: any) {
      setError(err.message || "Delete failed");
    }
  }

  function openEdit(trade: Trade) {
    setEditTrade(trade);
    setEditQty(String(trade.quantity));
    setEditSl(trade.stopLoss != null ? String(trade.stopLoss) : "");
    setEditTp(trade.takeProfit != null ? String(trade.takeProfit) : "");
    setEditNotes(trade.notes ?? "");
    setEditError(null);
  }

  async function handleEditSave() {
    if (!editTrade) return;
    const qty = Number(editQty);
    if (editTrade.status === "open" && (!Number.isInteger(qty) || qty < 1)) {
      setEditError("Quantity must be a whole number ≥ 1");
      return;
    }
    setSavingEdit(true);
    setEditError(null);
    try {
      const updated = await updateTrade(editTrade.id, {
        notes: editNotes || null,
        ...(editTrade.status === "open"
          ? {
              quantity: qty,
              stopLoss: editSl === "" ? null : Number(editSl),
              takeProfit: editTp === "" ? null : Number(editTp),
            }
          : {}),
      });
      setTrades((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      setEditTrade(null);
    } catch (err: any) {
      setEditError(err.message || "Update failed");
    } finally {
      setSavingEdit(false);
    }
  }

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
    <div className="mx-auto w-full max-w-6xl space-y-6">
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

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="flex items-center gap-2 p-4">
            <XCircle className="h-4 w-4 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">
                Unrealized P&amp;L
              </p>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className={`text-2xl font-semibold tabular-nums ${pnlClass(summary.runningPnl)}`}>
              {formatSignedInr(summary.runningPnl)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Open positions
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

      {/* Add trade form */}
      <Card>
        <CardContent className="p-5">
          <div className="grid grid-cols-2 items-end gap-3 xl:flex xl:flex-wrap">
            <div className="col-span-2 min-w-0 xl:w-48">
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Ticker</label>
              <TickerInput
                value={addTicker}
                onChange={(value) => {
                  setAddTicker(value);
                  if (value !== quoteTicker) {
                    setQuoteTicker("");
                    setQuote(null);
                    setAddError(null);
                  }
                }}
                onCommit={(symbol) => {
                  setAddTicker(symbol);
                  setQuoteTicker(symbol);
                }}
                placeholder="e.g. RELIANCE"
                disabled={adding}
              />
            </div>
            <div className="min-w-0 xl:w-24">
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Qty</label>
              <Input
                type="number"
                min="1"
                value={addQty}
                onChange={(e) => setAddQty(e.target.value)}
                disabled={adding || !quote}
              />
            </div>
            <div className="min-w-0 xl:w-28">
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">SL</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={addSl}
                onChange={(e) => setAddSl(e.target.value)}
                disabled={adding || !quote}
              />
            </div>
            <div className="min-w-0 xl:w-28">
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">TP</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={addTp}
                onChange={(e) => setAddTp(e.target.value)}
                disabled={adding || !quote}
              />
            </div>
            <div className="col-span-2 min-w-0 xl:min-w-[120px] xl:flex-1">
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Notes</label>
              <Input
                value={addNotes}
                onChange={(e) => setAddNotes(e.target.value)}
                placeholder="optional"
                disabled={adding}
              />
            </div>
            <Button
              className="col-span-2 xl:w-auto"
              onClick={handleAdd}
              disabled={!quote || adding}
            >
              {adding ? (
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-1 h-4 w-4" />
              )}
              Add
            </Button>
          </div>
          {quoting && (
            <p className="mt-2 text-xs text-muted-foreground">Fetching quote...</p>
          )}
          {addError && (
            <p className="mt-2 text-xs text-destructive">{addError}</p>
          )}
        </CardContent>
      </Card>

      {/* Filter pills */}
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

      {loading ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="mb-3 h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading trades...</p>
          </CardContent>
        </Card>
      ) : visible.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <CandlestickChart className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No trades match this filter.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-3 lg:hidden">
            {visible.map((trade) => {
              const pnl = tradePnl(trade);
              const pct = tradePnlPct(trade);
              return (
                <Card key={trade.id}>
                  <CardContent className="space-y-3 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-foreground">
                          {trade.ticker}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {trade.name}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <OutcomeBadge trade={trade} />
                        <TradeActions
                          trade={trade}
                          onEdit={openEdit}
                          onClose={setCloseTrade}
                          onDelete={setDeleteTrade}
                        />
                      </div>
                    </div>
                    <dl className="grid grid-cols-3 gap-x-3 gap-y-2 text-xs">
                      <div>
                        <dt className="text-muted-foreground">Opened</dt>
                        <dd className="tabular-nums text-foreground">
                          {formatDayMonth(trade.openedAt)}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Qty</dt>
                        <dd className="tabular-nums text-foreground">
                          {trade.quantity.toLocaleString("en-IN")}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Entry</dt>
                        <dd className="tabular-nums text-foreground">
                          {formatPrice(trade.entryPrice)}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Avg. price</dt>
                        <dd className="tabular-nums text-foreground">
                          {formatPrice(tradeMark(trade))}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Capital</dt>
                        <dd className="tabular-nums text-foreground">
                          {formatInr(tradeCapital(trade))}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">P&amp;L</dt>
                        <dd className={`tabular-nums font-medium ${pnlClass(pnl)}`}>
                          {pnl == null ? "—" : formatSignedInr(pnl)}
                          {pct != null && (
                            <span className="ml-1 font-normal">
                              ({pct > 0 ? "+" : ""}
                              {pct.toFixed(1)}%)
                            </span>
                          )}
                        </dd>
                      </div>
                    </dl>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card className="hidden overflow-x-auto lg:block">
            <table className="w-full table-fixed text-left text-sm">
              <colgroup>
                <col />
                <col className="w-[5.5rem]" />
                <col className="w-[5rem]" />
                <col className="w-[4.5rem]" />
                <col className="w-[6rem]" />
                <col className="w-[7rem]" />
                <col className="w-[6.5rem]" />
                <col className="w-[8.5rem]" />
                <col className="w-[5.5rem]" />
                <col className="w-[10.5rem]" />
              </colgroup>
              <thead>
                <tr className="border-b border-border">
                  {(
                    [
                      ["ticker", "Ticker", ""],
                      ["openedAt", "Opened", ""],
                      [null, "Side", ""],
                      ["quantity", "Qty", ""],
                      ["entryPrice", "Entry", ""],
                      [null, "Avg. price", ""],
                      ["capital", "Capital", ""],
                      ["pnl", "P&L", ""],
                      [null, "Outcome", ""],
                      [null, "", "text-left"],
                    ] as [SortKey | null, string, string][]
                  ).map(([key, label, extra], i) => (
                    <th
                      key={`${label}-${i}`}
                      className={`whitespace-nowrap px-2 py-2.5 first:pl-4 last:pr-4 ${extra || "text-center"}`}
                    >
                      {key ? (
                        <button
                          type="button"
                          onClick={() => handleSort(key)}
                          className="inline-flex items-center justify-center gap-1 font-medium text-muted-foreground transition-colors hover:text-foreground"
                        >
                          {label}
                          <SortIcon
                            active={sortCol === key}
                            asc={sortAsc}
                          />
                        </button>
                      ) : label ? (
                        <span className="font-medium text-muted-foreground">
                          {label}
                        </span>
                      ) : null}
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
                      className="group border-b border-border/50 transition-colors hover:bg-muted/50"
                    >
                      <td className="px-2 py-2 first:pl-4">
                        <p className="truncate font-medium text-foreground">
                          {trade.ticker}
                        </p>
                        <p className="max-w-[9rem] truncate text-xs text-muted-foreground">
                          {trade.name}
                        </p>
                      </td>
                      <td className="whitespace-nowrap px-2 py-2 text-center text-muted-foreground">
                        {formatDayMonth(trade.openedAt)}
                      </td>
                      <td className="px-2 py-2 text-center">
                        <Badge
                          variant={
                            trade.side === "long" ? "success" : "destructive"
                          }
                        >
                          {trade.side === "long" ? "Long" : "Short"}
                        </Badge>
                      </td>
                      <td className="px-2 py-2 text-center tabular-nums text-muted-foreground">
                        {trade.quantity.toLocaleString("en-IN")}
                      </td>
                      <td className="px-2 py-2 text-center tabular-nums text-muted-foreground">
                        {formatPrice(trade.entryPrice)}
                      </td>
                      <td className="px-2 py-2 text-center tabular-nums text-muted-foreground">
                        {formatPrice(tradeMark(trade))}
                      </td>
                      <td className="px-2 py-2 text-center tabular-nums text-muted-foreground">
                        {formatInr(tradeCapital(trade))}
                      </td>
                      <td
                        className={`whitespace-nowrap px-2 py-2 text-center tabular-nums font-medium ${pnlClass(pnl)}`}
                      >
                        {pnl == null ? "—" : formatSignedInr(pnl)}
                        {pct != null && (
                          <span className="ml-1 text-xs font-normal">
                            ({pct > 0 ? "+" : ""}
                            {pct.toFixed(1)}%)
                          </span>
                        )}
                      </td>
                      <td className="px-2 py-2 text-center">
                        <OutcomeBadge trade={trade} />
                      </td>
                      <td className="px-2 py-2 text-left last:pr-4">
                        <TradeActions
                          trade={trade}
                          onEdit={openEdit}
                          onClose={setCloseTrade}
                          onDelete={setDeleteTrade}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </>
      )}

      {/* Close confirm dialog */}
      <ConfirmDialog
        open={closeTrade_ !== null}
        onOpenChange={(open) => { if (!open) setCloseTrade(null); }}
        title="Close trade"
        description={
          closeTrade_
            ? `Exit ${closeTrade_.ticker} at ₹${formatPrice(closeTrade_.currentPrice)} as manual?`
            : ""
        }
        confirmLabel="Close"
        onConfirm={handleClose}
      />
      <ConfirmDialog
        open={deleteTrade_ !== null}
        onOpenChange={(open) => { if (!open) setDeleteTrade(null); }}
        title="Delete trade"
        description={
          deleteTrade_
            ? `Remove ${deleteTrade_.ticker} from the journal? This cannot be undone.`
            : ""
        }
        confirmLabel="Delete"
        onConfirm={handleDelete}
      />
      <Dialog
        open={editTrade !== null}
        onOpenChange={(open) => { if (!open) setEditTrade(null); }}
      >
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>
              {editTrade ? `Edit ${editTrade.ticker}` : "Edit trade"}
            </DialogTitle>
          </DialogHeader>
          {editTrade?.status === "open" ? (
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Qty</label>
                <Input
                  type="number"
                  min="1"
                  value={editQty}
                  onChange={(e) => setEditQty(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">SL</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editSl}
                  onChange={(e) => setEditSl(e.target.value)}
                  placeholder="none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">TP</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editTp}
                  onChange={(e) => setEditTp(e.target.value)}
                  placeholder="none"
                />
              </div>
            </div>
          ) : null}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Notes</label>
            <Input
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
              placeholder="optional"
            />
          </div>
          {editError ? (
            <p className="text-xs text-destructive">{editError}</p>
          ) : null}
          <DialogFooter>
            <Button variant="secondary" onClick={() => setEditTrade(null)}>
              Cancel
            </Button>
            <Button onClick={handleEditSave} disabled={savingEdit}>
              {savingEdit ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : null}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

import { request } from "./client";

export type TradeSide = "long" | "short";
export type TradeStatus = "open" | "closed";
export type CloseReason = "tp" | "sl" | "manual";

export interface Trade {
  id: string;
  ticker: string;
  name: string;
  side: TradeSide;
  status: TradeStatus;
  entryPrice: number;
  quantity: number;
  stopLoss: number | null;
  takeProfit: number | null;
  openedAt: string;
  closedAt: string | null;
  closeReason: CloseReason | null;
  exitPrice: number | null;
  currentPrice: number | null;
  notes: string | null;
}

export interface TradeQuote {
  ticker: string;
  name: string;
  ltp: number;
  quantity: number;
  stopLoss: number;
  takeProfit: number;
}

export interface TradeSummary {
  runningPnl: number;
  realizedPnl: number;
  totalPnl: number;
  capitalDeployed: number;
  openCount: number;
  closedCount: number;
  closedBy: Record<CloseReason, number>;
  winCount: number;
  lossCount: number;
}

const DIRECTION: Record<TradeSide, number> = { long: 1, short: -1 };

export function tradeCapital(trade: Trade): number {
  return trade.entryPrice * trade.quantity;
}

export function tradeMark(trade: Trade): number | null {
  if (trade.status === "closed") return trade.exitPrice;
  return trade.currentPrice;
}

export function tradePnl(trade: Trade): number | null {
  const mark = tradeMark(trade);
  if (mark == null) return null;
  return (mark - trade.entryPrice) * trade.quantity * DIRECTION[trade.side];
}

export function tradePnlPct(trade: Trade): number | null {
  const pnl = tradePnl(trade);
  const capital = tradeCapital(trade);
  if (pnl == null || capital === 0) return null;
  return (pnl / capital) * 100;
}

export function summarizeTrades(trades: Trade[]): TradeSummary {
  const closedBy: Record<CloseReason, number> = { tp: 0, sl: 0, manual: 0 };
  let runningPnl = 0;
  let realizedPnl = 0;
  let capitalDeployed = 0;
  let openCount = 0;
  let closedCount = 0;
  let winCount = 0;
  let lossCount = 0;

  for (const trade of trades) {
    const pnl = tradePnl(trade) ?? 0;
    if (trade.status === "open") {
      openCount += 1;
      runningPnl += pnl;
      capitalDeployed += tradeCapital(trade);
    } else {
      closedCount += 1;
      realizedPnl += pnl;
      if (trade.closeReason) closedBy[trade.closeReason] += 1;
      if (pnl > 0) winCount += 1;
      else if (pnl < 0) lossCount += 1;
    }
  }

  return {
    runningPnl,
    realizedPnl,
    totalPnl: runningPnl + realizedPnl,
    capitalDeployed,
    openCount,
    closedCount,
    closedBy,
    winCount,
    lossCount,
  };
}

export async function getTrades(): Promise<Trade[]> {
  const data = await request<{ trades: Trade[] }>("/trades");
  return data.trades;
}

export async function getTradeQuote(ticker: string): Promise<TradeQuote> {
  return request(`/trades/quote?ticker=${encodeURIComponent(ticker)}`);
}

export async function createTrade(body: {
  ticker: string;
  quantity: number;
  stopLoss: number;
  takeProfit: number;
  notes?: string;
}): Promise<Trade> {
  return request("/trades", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function closeTrade(
  id: string,
  body: { reason: "manual"; exitPrice: number },
): Promise<Trade> {
  return request(`/trades/${id}/close`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function deleteTrade(id: string): Promise<void> {
  const res = await fetch(`/api/v1/trades/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `API error: ${res.status}`);
  }
}

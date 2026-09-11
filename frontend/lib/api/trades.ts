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

// Sample journal until a trades API exists.
const MOCK_TRADES: Trade[] = [
  {
    id: "trd-008",
    ticker: "RELIANCE",
    name: "Reliance Industries",
    side: "long",
    status: "open",
    entryPrice: 1398,
    quantity: 80,
    stopLoss: 1335,
    takeProfit: 1510,
    openedAt: "2026-09-04T09:21:00+05:30",
    closedAt: null,
    closeReason: null,
    exitPrice: null,
    currentPrice: 1442,
    notes: "Breakout hold above 1380. Trailing toward first target.",
  },
  {
    id: "trd-007",
    ticker: "INFY",
    name: "Infosys",
    side: "long",
    status: "open",
    entryPrice: 1520,
    quantity: 60,
    stopLoss: 1462,
    takeProfit: 1625,
    openedAt: "2026-09-02T10:05:00+05:30",
    closedAt: null,
    closeReason: null,
    exitPrice: null,
    currentPrice: 1478,
    notes: "Pulled back to 20-DMA. Invalidates below stop.",
  },
  {
    id: "trd-006",
    ticker: "TATASTEEL",
    name: "Tata Steel",
    side: "long",
    status: "open",
    entryPrice: 168,
    quantity: 400,
    stopLoss: 159.5,
    takeProfit: 184,
    openedAt: "2026-08-28T13:40:00+05:30",
    closedAt: null,
    closeReason: null,
    exitPrice: null,
    currentPrice: 171.5,
    notes: null,
  },
  {
    id: "trd-005",
    ticker: "ITC",
    name: "ITC",
    side: "long",
    status: "closed",
    entryPrice: 412,
    quantity: 200,
    stopLoss: 395,
    takeProfit: 441,
    openedAt: "2026-08-12T09:18:00+05:30",
    closedAt: "2026-08-26T14:52:00+05:30",
    closeReason: "tp",
    exitPrice: 441,
    currentPrice: null,
    notes: "First target filled in full.",
  },
  {
    id: "trd-004",
    ticker: "INOXINDIA",
    name: "INOX India",
    side: "long",
    status: "closed",
    entryPrice: 1180,
    quantity: 50,
    stopLoss: 1112,
    takeProfit: 1295,
    openedAt: "2026-08-06T11:02:00+05:30",
    closedAt: "2026-08-22T10:14:00+05:30",
    closeReason: "tp",
    exitPrice: 1295,
    currentPrice: null,
    notes: null,
  },
  {
    id: "trd-003",
    ticker: "HDFCBANK",
    name: "HDFC Bank",
    side: "long",
    status: "closed",
    entryPrice: 1640,
    quantity: 40,
    stopLoss: 1580,
    takeProfit: 1750,
    openedAt: "2026-07-29T09:32:00+05:30",
    closedAt: "2026-08-18T15:10:00+05:30",
    closeReason: "manual",
    exitPrice: 1688,
    currentPrice: null,
    notes: "Booked ahead of results. Did not wait for TP.",
  },
  {
    id: "trd-002",
    ticker: "DELHIVERY",
    name: "Delhivery",
    side: "long",
    status: "closed",
    entryPrice: 385,
    quantity: 150,
    stopLoss: 352,
    takeProfit: 430,
    openedAt: "2026-07-21T10:44:00+05:30",
    closedAt: "2026-08-04T09:47:00+05:30",
    closeReason: "sl",
    exitPrice: 352,
    currentPrice: null,
    notes: "Failed hold of support. Stopped out.",
  },
  {
    id: "trd-001",
    ticker: "WIPRO",
    name: "Wipro",
    side: "long",
    status: "closed",
    entryPrice: 265,
    quantity: 200,
    stopLoss: 248,
    takeProfit: 292,
    openedAt: "2026-07-08T09:16:00+05:30",
    closedAt: "2026-07-17T13:22:00+05:30",
    closeReason: "sl",
    exitPrice: 248,
    currentPrice: null,
    notes: null,
  },
];

export async function getTrades(): Promise<Trade[]> {
  return MOCK_TRADES;
}

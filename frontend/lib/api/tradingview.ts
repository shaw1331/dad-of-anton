import { request } from "./client";

export interface Candle {
  datetime: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandlesResponse {
  symbol: string;
  exchange: string;
  interval: string;
  candles: Candle[];
}

export function getCandles(
  symbol: string,
  exchange: string = "NSE",
  interval: string = "1D",
  bars: number = 30
): Promise<CandlesResponse> {
  const params = new URLSearchParams({
    symbol: symbol.toUpperCase(),
    exchange: exchange.toUpperCase(),
    interval,
    bars: String(bars),
  });
  return request<CandlesResponse>(`/tradingview/candles?${params}`);
}

import { request } from "./client";

export interface StockEntry {
  symbol: string;
  name: string;
}

export function searchStocks(
  query: string,
  limit: number = 10
): Promise<StockEntry[]> {
  return request<StockEntry[]>(
    `/stocks/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
}

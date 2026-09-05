import { request } from "./client";

export interface TrendlyneStock {
  ticker: string;
  name: string;
  company_name: string;
  sector: string | null;
  industry: string | null;
  source: string;
  data: Record<string, number>;
  url: string;
  scraped_at: string | null;
}

export interface TrendlyneResult {
  ticker: string;
  stock: TrendlyneStock;
  took_ms: number;
}

export function fetchTrendlyneTechnicals(
  ticker: string
): Promise<TrendlyneResult> {
  return request<TrendlyneResult>(
    `/trendlyne?ticker=${encodeURIComponent(ticker)}`
  );
}

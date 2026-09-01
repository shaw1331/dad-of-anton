import { request } from "./client";

export interface ScreenerMeta {
  name: string;
  description: string;
}

export interface ScreenerResult {
  screener: string;
  columns: string[];
  rows: Record<string, string | number>[];
  count: number;
  took_ms: number;
}

export function getScreeners(): Promise<ScreenerMeta[]> {
  return request<ScreenerMeta[]>("/nse-screener/screeners");
}

export function runScreener(screener: string): Promise<ScreenerResult> {
  return request<ScreenerResult>("/nse-screener/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screener }),
  });
}

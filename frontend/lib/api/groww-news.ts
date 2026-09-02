import { request } from "./client";

export interface GrowwNewsArticle {
  id: string;
  summary: string;
  url: string;
  image_url: string | null;
  pub_date: string;
  source: string;
}

export interface GrowwNewsResult {
  ticker: string;
  groww_contract_id: string;
  company_name: string;
  articles: GrowwNewsArticle[];
  count: number;
  took_ms: number;
}

export function fetchGrowwNews(
  ticker: string,
  days: number = 15
): Promise<GrowwNewsResult> {
  return request<GrowwNewsResult>(
    `/groww-news?ticker=${encodeURIComponent(ticker)}&days=${days}`
  );
}

"use client";

import { useState } from "react";
import { Search, ExternalLink, Newspaper } from "lucide-react";
import {
  fetchGrowwNews,
  GrowwNewsArticle,
  GrowwNewsResult,
} from "@/lib/api/groww-news";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Input } from "@/components/ui/input";

export default function GrowwNewsPage() {
  const [ticker, setTicker] = useState("");
  const [daysStr, setDaysStr] = useState("15");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GrowwNewsResult | null>(null);

  const days = Math.min(90, Math.max(1, parseInt(daysStr, 10) || 15));

  async function handleSearch() {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await fetchGrowwNews(ticker.trim(), days);
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch news");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleSearch();
  }

  function formatDate(dateStr: string): string {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Groww News
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Fetch recent stock news from Groww. Enter a ticker (e.g. ITC,
          DELHIVERY) and set the lookback period.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[240px] flex-1">
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Ticker
              </label>
              <Input
                placeholder="e.g. ITC, DELHIVERY, INFY..."
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
            </div>
            <div className="w-[120px]">
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Days
              </label>
              <Input
                type="number"
                min={1}
                max={90}
                value={daysStr}
                onChange={(e) => setDaysStr(e.target.value)}
                disabled={loading}
              />
            </div>
            <Button onClick={handleSearch} disabled={loading || !ticker.trim()}>
              {loading ? (
                <>
                  <Spinner size="sm" className="text-primary-foreground" />
                  Fetching...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Search News
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="p-4">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12">
            <Spinner size="lg" />
            <p className="text-sm text-muted-foreground">
              Fetching news from Groww...
            </p>
          </CardContent>
        </Card>
      )}

      {result && !loading && (
        <>
          <div className="flex items-center gap-3">
            <Badge variant="info">{result.company_name}</Badge>
            <Badge variant="muted">{result.count} articles</Badge>
            <Badge variant="muted">
              {(result.took_ms / 1000).toFixed(1)}s
            </Badge>
          </div>

          {result.articles.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <Newspaper className="mb-3 h-10 w-10 text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">
                  No news found for {result.ticker} in the last 15 days.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {result.articles.map((article: GrowwNewsArticle) => (
                <Card key={article.id}>
                  <CardContent className="p-5">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm leading-relaxed text-foreground">
                          {article.summary}
                        </p>
                        {article.url && (
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="shrink-0 text-muted-foreground transition-colors hover:text-foreground"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="muted" className="text-xs">
                          {article.source}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(article.pub_date)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {!loading && !error && !result && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Newspaper className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Enter a stock ticker to fetch recent news from Groww.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { Search, BarChart3 } from "lucide-react";
import {
  fetchTrendlyneTechnicals,
  TrendlyneResult,
} from "@/lib/api/trendlyne";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Input } from "@/components/ui/input";
import {
  CollapsibleSection,
  DataRow,
} from "@/components/ui/collapsible-section";

const EMA_FIELDS: [string, string][] = [
  ["ema_5", "5 Day"],
  ["ema_10", "10 Day"],
  ["ema_12", "12 Day"],
  ["ema_20", "20 Day"],
  ["ema_26", "26 Day"],
  ["ema_50", "50 Day"],
  ["ema_100", "100 Day"],
  ["ema_200", "200 Day"],
];

const SMA_FIELDS: [string, string][] = [
  ["sma_5", "5 Day"],
  ["sma_10", "10 Day"],
  ["sma_20", "20 Day"],
  ["sma_30", "30 Day"],
  ["sma_50", "50 Day"],
  ["sma_100", "100 Day"],
  ["sma_150", "150 Day"],
  ["sma_200", "200 Day"],
];

const MOMENTUM_FIELDS: [string, string][] = [
  ["rsi", "RSI"],
  ["macd", "MACD"],
  ["macd_signal", "MACD Signal Line"],
  ["adx", "ADX"],
  ["atr", "ATR"],
  ["mfi", "MFI"],
  ["cci", "CCI"],
  ["roc_21", "ROC (21)"],
  ["roc_125", "ROC (125)"],
  ["williams_r", "Williams %R"],
];

const SR_FIELDS: [string, string][] = [
  ["pivot", "Pivot"],
  ["r1", "R1"],
  ["r2", "R2"],
  ["r3", "R3"],
  ["s1", "S1"],
  ["s2", "S2"],
  ["s3", "S3"],
];

const RETURN_FIELDS: [string, string][] = [
  ["return_1m", "1 Month"],
  ["return_3m", "3 Months"],
  ["return_6m", "6 Months"],
  ["return_1y", "1 Year"],
];

const VOLUME_FIELDS: [string, string][] = [
  ["vol_day", "Day"],
  ["vol_week", "Week"],
  ["vol_month", "Month"],
];

const BETA_FIELDS: [string, string][] = [
  ["beta_1m", "1 Month"],
  ["beta_3m", "3 Months"],
  ["beta_1y", "1 Year"],
  ["beta_3y", "3 Years"],
];

function formatValue(key: string, value: number | undefined | null): string {
  if (value == null) return "N/A";
  if (key.startsWith("return_")) return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
  if (key === "rsi" || key === "adx" || key === "mfi" || key === "cci" || key === "williams_r")
    return value.toFixed(1);
  if (key.startsWith("vol_")) return value.toLocaleString("en-IN");
  return value.toFixed(2);
}

export default function TrendlynePage() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TrendlyneResult | null>(null);

  async function handleSearch() {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await fetchTrendlyneTechnicals(ticker.trim());
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch technicals");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleSearch();
  }

  function renderRows(fields: [string, string][], data: Record<string, number>) {
    return fields.map(([key, label]) => (
      <DataRow key={key} label={label} value={formatValue(key, data[key])} />
    ));
  }

  function hasData(fields: [string, string][], data: Record<string, number>) {
    return fields.some(([key]) => data[key] != null);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Trendlyne Technicals
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Fetch technical indicators (EMA, SMA, RSI, MACD, etc.) from Trendlyne.
          Enter a ticker (e.g. ITC, RELIANCE).
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
                placeholder="e.g. ITC, RELIANCE, INFY..."
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                onKeyDown={handleKeyDown}
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
                  Search Technicals
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
              Fetching technicals from Trendlyne...
            </p>
          </CardContent>
        </Card>
      )}

      {result && !loading && (
        <>
          <div className="flex items-center gap-3">
            <Badge variant="info">{result.stock.name}</Badge>
            <Badge variant="muted">{result.stock.ticker}</Badge>
            <Badge variant="muted">{(result.took_ms / 1000).toFixed(1)}s</Badge>
            {result.stock.url && (
              <a
                href={result.stock.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-muted-foreground underline-offset-4 hover:underline"
              >
                View on Trendlyne
              </a>
            )}
          </div>

          <div className="space-y-3">
            {hasData(EMA_FIELDS, result.stock.data) && (
              <CollapsibleSection title="EMA" defaultOpen>
                {renderRows(EMA_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}

            {hasData(SMA_FIELDS, result.stock.data) && (
              <CollapsibleSection title="SMA">
                {renderRows(SMA_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}

            {hasData(MOMENTUM_FIELDS, result.stock.data) && (
              <CollapsibleSection title="Momentum" defaultOpen>
                {renderRows(MOMENTUM_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}

            {hasData(SR_FIELDS, result.stock.data) && (
              <CollapsibleSection title="Support / Resistance">
                {renderRows(SR_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}

            {hasData(RETURN_FIELDS, result.stock.data) && (
              <CollapsibleSection title="Price Returns">
                {renderRows(RETURN_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}

            {hasData(VOLUME_FIELDS, result.stock.data) && (
              <CollapsibleSection title="Volume">
                {renderRows(VOLUME_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}

            {hasData(BETA_FIELDS, result.stock.data) && (
              <CollapsibleSection title="Beta">
                {renderRows(BETA_FIELDS, result.stock.data)}
              </CollapsibleSection>
            )}
          </div>
        </>
      )}

      {!loading && !error && !result && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <BarChart3 className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Enter a stock ticker to fetch technical indicators from Trendlyne.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

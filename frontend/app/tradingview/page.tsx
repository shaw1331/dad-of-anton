"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { getCandles, Candle } from "@/lib/api/tradingview";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";

export default function TradingViewPage() {
  const [symbol, setSymbol] = useState("");
  const [exchange, setExchange] = useState("NSE");
  const [interval, setInterval] = useState("1D");
  const [bars, setBars] = useState(30);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<{ symbol: string; exchange: string; interval: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim()) return;

    setLoading(true);
    setError(null);
    setCandles([]);
    setMeta(null);

    try {
      const res = await getCandles(symbol.trim(), exchange, interval, bars);
      setCandles(res.candles);
      setMeta({ symbol: res.symbol, exchange: res.exchange, interval: res.interval });
    } catch (err: any) {
      setError(err.message || "Failed to fetch candles");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          TradingView Candles
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Fetch OHLCV candle data from TradingView for any listed symbol.
        </p>
      </div>

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-4">
            <div className="min-w-[200px] flex-1">
              <Label htmlFor="symbol" className="mb-1.5">Stock Symbol</Label>
              <Input
                id="symbol"
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="e.g. INOXINDIA"
                required
              />
            </div>
            <div className="min-w-[140px]">
              <Label className="mb-1.5">Exchange</Label>
              <Select value={exchange} onValueChange={setExchange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NSE">NSE</SelectItem>
                  <SelectItem value="BSE">BSE</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="min-w-[140px]">
              <Label className="mb-1.5">Interval</Label>
              <Select value={interval} onValueChange={setInterval}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1m</SelectItem>
                  <SelectItem value="5">5m</SelectItem>
                  <SelectItem value="15">15m</SelectItem>
                  <SelectItem value="60">1h</SelectItem>
                  <SelectItem value="240">4h</SelectItem>
                  <SelectItem value="1D">1D</SelectItem>
                  <SelectItem value="1W">1W</SelectItem>
                  <SelectItem value="1M">1M</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-24">
              <Label htmlFor="bars" className="mb-1.5">Bars</Label>
              <Input
                id="bars"
                type="number"
                value={bars}
                onChange={(e) => setBars(Number(e.target.value))}
                min={1}
                max={500}
              />
            </div>
            <Button type="submit" disabled={loading || !symbol.trim()}>
              {loading ? (
                <>
                  <Spinner size="sm" className="text-primary-foreground" />
                  Loading...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Fetch
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="p-4">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading && !candles.length && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12">
            <Spinner size="lg" />
            <p className="text-sm text-muted-foreground">
              Fetching candle data...
            </p>
          </CardContent>
        </Card>
      )}

      {meta && candles.length > 0 && (
        <Card>
          <div className="px-6 pt-6">
            <div className="mb-4 flex items-center gap-3">
              <h2 className="text-lg font-semibold text-foreground">
                {meta.exchange}:{meta.symbol}
              </h2>
              <Badge variant="info">{meta.interval}</Badge>
              <Badge variant="muted">{candles.length} bars</Badge>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">
                    Open
                  </th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">
                    High
                  </th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">
                    Low
                  </th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">
                    Close
                  </th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">
                    Volume
                  </th>
                </tr>
              </thead>
              <tbody>
                {[...candles].reverse().map((c, i) => {
                  const change = c.close - c.open;
                  const changeColor =
                    change > 0
                      ? "text-emerald-600 dark:text-emerald-400"
                      : change < 0
                        ? "text-red-600 dark:text-red-400"
                        : "";
                  return (
                    <tr
                      key={i}
                      className="border-b border-border/50 transition-colors hover:bg-muted/50"
                    >
                      <td className="whitespace-nowrap px-4 py-2.5 text-foreground">
                        {c.datetime}
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-muted-foreground">
                        {c.open.toFixed(2)}
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-muted-foreground">
                        {c.high.toFixed(2)}
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-muted-foreground">
                        {c.low.toFixed(2)}
                      </td>
                      <td className={`px-4 py-2.5 tabular-nums font-medium ${changeColor || "text-muted-foreground"}`}>
                        {c.close.toFixed(2)}
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-muted-foreground">
                        {c.volume.toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {!loading && !error && candles.length === 0 && meta === null && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Enter a stock symbol and click Fetch to load candle data.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

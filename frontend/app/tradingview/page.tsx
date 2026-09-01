"use client";

import { useState } from "react";
import { getCandles, Candle } from "@/lib/api/tradingview";

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
      <h1 className="text-2xl font-bold text-slate-900 dark:text-[#EDEDED]">
        TradingView Candles
      </h1>

      <form onSubmit={handleSubmit} className="card flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-[#888888]">
            Stock Symbol
          </label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="e.g. INOXINDIA"
            className="input-field"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-[#888888]">
            Exchange
          </label>
          <select
            value={exchange}
            onChange={(e) => setExchange(e.target.value)}
            className="input-field"
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-[#888888]">
            Interval
          </label>
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="input-field"
          >
            <option value="1">1m</option>
            <option value="5">5m</option>
            <option value="15">15m</option>
            <option value="60">1h</option>
            <option value="240">4h</option>
            <option value="1D">1D</option>
            <option value="1W">1W</option>
            <option value="1M">1M</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-[#888888]">
            Bars
          </label>
          <input
            type="number"
            value={bars}
            onChange={(e) => setBars(Number(e.target.value))}
            min={1}
            max={500}
            className="input-field w-20"
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? "Loading..." : "Fetch"}
        </button>
      </form>

      {error && (
        <div className="card border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {meta && candles.length > 0 && (
        <div className="card">
          <div className="mb-4 flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-[#EDEDED]">
              {meta.exchange}:{meta.symbol}
            </h2>
            <span className="badge badge-info">{meta.interval}</span>
            <span className="badge badge-muted">{candles.length} bars</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-white/10">
                    <th className="px-3 py-2 font-medium text-slate-600 dark:text-[#888888]">
                      Date
                    </th>
                    <th className="px-3 py-2 font-medium text-slate-600 dark:text-[#888888]">
                      Open
                    </th>
                    <th className="px-3 py-2 font-medium text-slate-600 dark:text-[#888888]">
                      High
                    </th>
                    <th className="px-3 py-2 font-medium text-slate-600 dark:text-[#888888]">
                      Low
                    </th>
                    <th className="px-3 py-2 font-medium text-slate-600 dark:text-[#888888]">
                      Close
                    </th>
                    <th className="px-3 py-2 font-medium text-slate-600 dark:text-[#888888]">
                      Volume
                    </th>
                </tr>
              </thead>
              <tbody>
                {[...candles].reverse().map((c, i) => {
                  const change = c.close - c.open;
                  const changeColor =
                    change > 0
                      ? "text-green-600 dark:text-green-400"
                      : change < 0
                        ? "text-red-600 dark:text-red-400"
                        : "text-slate-600 dark:text-[#888888]";
                  return (
                    <tr
                      key={i}
                      className="border-b border-slate-100 transition-colors hover:bg-slate-50 dark:border-white/10 dark:hover:bg-[#111111]"
                    >
                        <td className="whitespace-nowrap px-3 py-2 text-slate-900 dark:text-[#EDEDED]">
                        {c.datetime}
                      </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-[#888888]">
                          {c.open.toFixed(2)}
                        </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-[#888888]">
                          {c.high.toFixed(2)}
                        </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-[#888888]">
                          {c.low.toFixed(2)}
                        </td>
                      <td className={`px-3 py-2 tabular-nums font-medium ${changeColor}`}>
                        {c.close.toFixed(2)}
                      </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-[#888888]">
                          {c.volume.toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && !error && candles.length === 0 && meta === null && (
        <div className="card text-center text-slate-500 dark:text-[#888888]">
          Enter a stock symbol and click Fetch to load candle data.
        </div>
      )}
    </div>
  );
}

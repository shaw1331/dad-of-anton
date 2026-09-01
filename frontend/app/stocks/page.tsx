"use client";

import { useState } from "react";
import { triggerWorkflow } from "@/lib/api/workflows";

export default function StocksPage() {
  const [tickers, setTickers] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = tickers
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (parsed.length === 0) {
      setError("Please enter at least one ticker");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await triggerWorkflow("stock_scraper", {
        tickers: parsed.join(","),
      });
      if (data.run_id) {
        window.location.href = `/home/${data.run_id}`;
      }
    } catch (err: any) {
      setError(err.message || "Failed to trigger workflow");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="page-header">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-[#EDEDED]">
          Stock Scraper
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-[#888888]">
          Enter stock tickers to scrape data from screener.in
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card max-w-lg">
        <label className="mb-1 block text-sm font-semibold text-gray-700 dark:text-[#888888]">
          Stock Tickers
          <span className="ml-1 text-red-500">*</span>
        </label>
        <p className="mb-3 text-xs text-slate-400 dark:text-slate-500">
          Comma-separated list (e.g. RELIANCE, TCS, INFY)
        </p>
        <input
          type="text"
          value={tickers}
          onChange={(e) => setTickers(e.target.value)}
          placeholder="RELIANCE, TCS, INFY"
          className="input-field"
        />
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary mt-5 w-full"
        >
          {loading ? (
            <>
              <svg
                className="h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Scraping...
            </>
          ) : (
            <>
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                />
              </svg>
              Scrape Stocks
            </>
          )}
        </button>
      </form>
    </div>
  );
}

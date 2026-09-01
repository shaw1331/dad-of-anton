"use client";

import { useState, useEffect, useRef } from "react";
import {
  getScreeners,
  runScreener,
  ScreenerMeta,
  ScreenerResult,
} from "@/lib/api/nse-screener";

export default function ScreenerPage() {
  const [screeners, setScreeners] = useState<ScreenerMeta[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScreenerResult | null>(null);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    getScreeners()
      .then((data) => {
        setScreeners(data);
        if (data.length > 0) setSelected(data[0].name);
      })
      .catch(() => setScreeners([]));
  }, []);

  const selectedMeta = screeners.find((s) => s.name === selected);

  async function handleRun() {
    if (!selected) return;

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await runScreener(selected);
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Screener failed");
    } finally {
      setLoading(false);
    }
  }

  function handleSort(col: string) {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
  }

  const sortedRows = (() => {
    if (!result) return [];
    const rows = [...result.rows];
    if (!sortCol) return rows;
    return rows.sort((a, b) => {
      const av = a[sortCol];
      const bv = b[sortCol];
      if (typeof av === "number" && typeof bv === "number") {
        return sortAsc ? av - bv : bv - av;
      }
      return sortAsc
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
  })();

  function downloadCsv() {
    if (!result) return;
    const header = result.columns.join(",");
    const csvRows = result.rows.map((r) =>
      result.columns.map((c) => r[c] ?? "").join(",")
    );
    const blob = new Blob([header + "\n" + csvRows.join("\n")], {
      type: "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `screener_${selected.replace(/\s+/g, "_").toLowerCase()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function formatValue(val: string | number, col: string): string {
    if (typeof val === "number") {
      if (col.toLowerCase().includes("vol")) {
        if (val >= 1e7) return (val / 1e7).toFixed(1) + "Cr";
        if (val >= 1e5) return (val / 1e5).toFixed(1) + "L";
        if (val >= 1e3) return (val / 1e3).toFixed(1) + "K";
        return val.toLocaleString();
      }
      return val.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }
    return String(val);
  }

  function getChangeColor(col: string, val: string | number): string {
    if (typeof val !== "number") return "";
    const lower = col.toLowerCase();
    if (lower.includes("chg") || lower.includes("rsi") || lower.includes("from")) {
      if (lower.includes("chg")) {
        return val > 0
          ? "text-green-600 dark:text-green-400"
          : val < 0
            ? "text-red-600 dark:text-red-400"
            : "";
      }
    }
    return "";
  }

  function getSortIcon(col: string) {
    if (sortCol !== col) return "text-slate-300 dark:text-slate-600";
    return "text-blue-500 dark:text-blue-400";
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-dark-text">
          NSE Screener
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-dark-muted">
          Screen 2500+ NSE stocks with pre-built scans. Pick a screener, hit
          run — results appear below.
        </p>
      </div>

      <div className="card flex flex-wrap items-end gap-4">
        <div className="min-w-[240px] flex-1">
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-dark-muted">
            Screener
          </label>
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="input-field"
            disabled={loading}
          >
            {screeners.length === 0 && <option>Loading...</option>}
            {screeners.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <button onClick={handleRun} disabled={loading || !selected} className="btn-primary">
          {loading ? (
            <>
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Scanning...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              Run Screener
            </>
          )}
        </button>
      </div>

      {selectedMeta && (
        <div className="rounded-xl border border-blue-200/60 bg-blue-50/50 px-5 py-3 text-sm text-blue-700 dark:border-blue-800/40 dark:bg-blue-900/20 dark:text-blue-300">
          <span className="font-semibold">{selectedMeta.name}</span> —{" "}
          {selectedMeta.description}
        </div>
      )}

      {error && (
        <div className="card border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {loading && (
        <div className="card flex flex-col items-center gap-3 py-12 text-slate-500 dark:text-dark-muted">
          <svg className="h-8 w-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-sm">
            Scanning 2500+ NSE stocks — this may take a minute...
          </p>
        </div>
      )}

      {result && !loading && (
        <>
          <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-dark-muted">
            <span className="badge badge-info">{result.count} stocks</span>
            <span className="badge badge-muted">
              {(result.took_ms / 1000).toFixed(1)}s
            </span>
            <span className="badge badge-muted">
              {new Date().toLocaleDateString("en-IN")}
            </span>
            <div className="flex-1" />
            <button onClick={downloadCsv} className="btn-ghost text-xs">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Download CSV
            </button>
          </div>

          <div className="card overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-dark-border">
                    <th className="px-4 py-3 font-medium text-slate-500 dark:text-dark-muted">
                      #
                    </th>
                    {result.columns.map((col) => (
                      <th
                        key={col}
                        onClick={() => handleSort(col)}
                        className="cursor-pointer select-none px-4 py-3 font-medium text-slate-500 transition-colors hover:text-slate-900 dark:text-dark-muted dark:hover:text-dark-text"
                      >
                        <span className="inline-flex items-center gap-1">
                          {col}
                          <svg
                            className={`h-3 w-3 ${getSortIcon(col)}`}
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={2}
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d={sortCol === col && !sortAsc ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"}
                            />
                          </svg>
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-slate-100 transition-colors hover:bg-slate-50 dark:border-dark-border dark:hover:bg-slate-800/50"
                    >
                      <td className="whitespace-nowrap px-4 py-2.5 text-slate-400 dark:text-slate-600">
                        {i + 1}
                      </td>
                      {result.columns.map((col) => (
                        <td
                          key={col}
                          className={`whitespace-nowrap px-4 py-2.5 tabular-nums ${
                            col === "Symbol"
                              ? "font-medium text-slate-900 dark:text-dark-text"
                              : `text-slate-700 dark:text-dark-muted ${getChangeColor(col, row[col])}`
                          }`}
                        >
                          {formatValue(row[col], col)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!loading && !error && !result && (
        <div className="card text-center text-slate-500 dark:text-dark-muted">
          Select a screener and click Run to scan NSE stocks.
        </div>
      )}
    </div>
  );
}

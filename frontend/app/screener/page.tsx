"use client";

import { useState, useEffect } from "react";
import { Search, ArrowUpDown, ArrowUp, ArrowDown, Download } from "lucide-react";
import {
  getScreeners,
  runScreener,
  ScreenerMeta,
  ScreenerResult,
} from "@/lib/api/nse-screener";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function ScreenerPage() {
  const [screeners, setScreeners] = useState<ScreenerMeta[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScreenerResult | null>(null);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

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
    if (col.toLowerCase().includes("chg")) {
      return val > 0
        ? "text-emerald-600 dark:text-emerald-400"
        : val < 0
          ? "text-red-600 dark:text-red-400"
          : "";
    }
    if (col === "RSI") {
      return val <= 30
        ? "text-amber-600 dark:text-amber-400"
        : val >= 70
          ? "text-red-600 dark:text-red-400"
          : "";
    }
    return "";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          NSE Screener
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Screen 2500+ NSE stocks with pre-built scans. Pick a screener, hit
          run — results appear below.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[240px] flex-1">
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Screener
              </label>
              <Select value={selected} onValueChange={setSelected} disabled={loading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a screener..." />
                </SelectTrigger>
                <SelectContent position="popper" className="z-[100]">
                  {screeners.map((s) => (
                    <SelectItem key={s.name} value={s.name}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleRun} disabled={loading || !selected}>
              {loading ? (
                <>
                  <Spinner size="sm" className="text-primary-foreground" />
                  Scanning...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Run Screener
                </>
              )}
            </Button>
          </div>
          {selectedMeta && (
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{selectedMeta.name}</span>{" "}
              — {selectedMeta.description}
            </p>
          )}
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
              Scanning 2500+ NSE stocks — this may take a minute...
            </p>
          </CardContent>
        </Card>
      )}

      {result && !loading && (
        <>
          <div className="flex items-center gap-3">
            <Badge variant="info">{result.count} stocks</Badge>
            <Badge variant="muted">
              {(result.took_ms / 1000).toFixed(1)}s
            </Badge>
            <Badge variant="muted">
              {new Date().toLocaleDateString("en-IN")}
            </Badge>
            <div className="flex-1" />
            <Button variant="ghost" size="sm" onClick={downloadCsv}>
              <Download className="h-4 w-4" />
              CSV
            </Button>
          </div>

          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 font-medium text-muted-foreground">
                      #
                    </th>
                    {result.columns.map((col) => (
                      <th
                        key={col}
                        onClick={() => handleSort(col)}
                        className="cursor-pointer select-none px-4 py-3 font-medium text-muted-foreground transition-colors hover:text-foreground"
                      >
                        <span className="inline-flex items-center gap-1">
                          {col}
                          {sortCol === col ? (
                            sortAsc ? (
                              <ArrowUp className="h-3 w-3 text-primary" />
                            ) : (
                              <ArrowDown className="h-3 w-3 text-primary" />
                            )
                          ) : (
                            <ArrowUpDown className="h-3 w-3 opacity-30" />
                          )}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-border/50 transition-colors hover:bg-muted/50"
                    >
                      <td className="whitespace-nowrap px-4 py-2.5 text-muted-foreground">
                        {i + 1}
                      </td>
                      {result.columns.map((col) => (
                        <td
                          key={col}
                          className={`whitespace-nowrap px-4 py-2.5 tabular-nums ${
                            col === "Symbol"
                              ? "font-medium text-foreground"
                              : `text-muted-foreground ${getChangeColor(col, row[col])}`
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
          </Card>
        </>
      )}

      {!loading && !error && !result && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              Select a screener and click Run to scan NSE stocks.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

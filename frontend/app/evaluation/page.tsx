"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { EvaluationSummary } from "@/lib/types";

export default function EvaluationPage() {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/evaluation/summary")
      .then((response) => response.json().then((body) => response.ok ? body : Promise.reject(new Error(body.detail))))
      .then(setSummary)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const scalarMetrics = Object.entries(summary?.metrics ?? {}).filter(([, value]) => value == null || typeof value === "number");
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold text-foreground">Jury evaluation</h1><p className="mt-1 text-sm text-muted-foreground">Historical prompt quality and release-gate metrics.</p></div>{error && <p className="rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}{summary && <Card><CardHeader><div className="flex items-center gap-3"><CardTitle className="text-base">Dataset status</CardTitle><Badge variant={summary.status === "ready" ? "success" : "warning"}>{summary.status}</Badge></div></CardHeader><CardContent className="space-y-4"><p className="text-sm text-muted-foreground">Required cases: {summary.required_cases}</p>{summary.status === "not_loaded" ? <p className="text-sm text-muted-foreground">Add a frozen dataset at the configured backend path before release evaluation.</p> : <><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{scalarMetrics.map(([key, value]) => <div key={key} className="rounded border border-border p-3"><p className="text-xs text-muted-foreground">{key.replaceAll("_", " ")}</p><p className="mt-1 text-lg font-semibold text-foreground">{value == null ? "—" : typeof value === "number" ? value.toFixed(3) : "—"}</p></div>)}</div>{summary.release_gate && <div className="rounded border border-border p-3 text-sm"><p className="font-medium text-foreground">Release gate: {summary.release_gate.passed ? "passed" : "blocked"}</p><p className="mt-1 text-muted-foreground">{Object.entries(summary.release_gate.checks).filter(([, passed]) => !passed).map(([name]) => name).join(", ") || "All checks passed."}</p></div>}</>}</CardContent></Card>}</div>;
}

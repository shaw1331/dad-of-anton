"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X, Play } from "lucide-react";
import { triggerWorkflow } from "@/lib/api/workflows";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type Candidate = { ticker: string; exchange: string };

export default function StockJuryPage() {
  const router = useRouter();
  const [symbol, setSymbol] = useState("");
  const [exchange, setExchange] = useState("NSE");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [workflow, setWorkflow] = useState("swing_momentum");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addCandidate() {
    const ticker = symbol.trim().toUpperCase();
    if (!ticker) return;
    if (candidates.some((candidate) => candidate.ticker === ticker && candidate.exchange === exchange)) {
      setError(`${ticker} is already selected`);
      return;
    }
    if (candidates.length >= 10) {
      setError("A jury run supports at most 10 stocks");
      return;
    }
    setCandidates([...candidates, { ticker, exchange }]);
    setSymbol("");
    setError(null);
  }

  async function start() {
    if (candidates.length < 2) {
      setError("Select at least 2 stocks");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await triggerWorkflow("stock_jury", {
        stocks: candidates,
        analysis_workflow: workflow,
        policy: { max_holdings: 3, max_allocation_pct: 50 },
      });
      router.push(`/workflows/${result.run_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start jury");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Stock Jury</h1>
        <p className="mt-1 text-sm text-muted-foreground">Compare selected stocks with independent analysts and a final chairperson.</p>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">Add candidate stocks</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[220px] flex-1">
              <Label htmlFor="jury-symbol" className="mb-1.5">Stock Symbol</Label>
              <Input id="jury-symbol" value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} onKeyDown={(event) => event.key === "Enter" && (event.preventDefault(), addCandidate())} placeholder="e.g. RELIANCE" />
            </div>
            <div className="w-32">
              <Label className="mb-1.5">Exchange</Label>
              <Select value={exchange} onValueChange={setExchange}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="NSE">NSE</SelectItem><SelectItem value="BSE">BSE</SelectItem></SelectContent></Select>
            </div>
            <Button type="button" onClick={addCandidate}><Plus className="h-4 w-4" /> Add</Button>
          </div>
          <div className="rounded-lg border border-border p-3">
            <div className="mb-2 flex items-center justify-between text-sm text-muted-foreground"><span>Selected stocks</span><Badge variant="muted">{candidates.length}/10</Badge></div>
            {candidates.length === 0 ? <p className="text-sm text-muted-foreground">Add at least two stocks to begin.</p> : <div className="space-y-2">{candidates.map((candidate) => <div key={`${candidate.exchange}:${candidate.ticker}`} className="flex items-center justify-between rounded bg-muted/50 px-3 py-2 text-sm"><span className="font-medium">{candidate.exchange}:{candidate.ticker}</span><Button variant="ghost" size="icon" onClick={() => setCandidates(candidates.filter((item) => item !== candidate))}><X className="h-4 w-4" /></Button></div>)}</div>}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-base">Analysis workflow</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Label>Workflow applied to every selected stock</Label>
          <Select value={workflow} onValueChange={setWorkflow}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="swing_momentum">Swing momentum (4–8 weeks)</SelectItem></SelectContent></Select>
          <p className="text-xs text-muted-foreground">Uses 60 daily candles, Trendlyne indicators, fundamentals, and recent news. Jury defaults: 1–3 holdings, 50% maximum per stock, cash allowed.</p>
        </CardContent>
      </Card>
      {error && <p className="rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
      <Button className="w-full" size="lg" disabled={busy || candidates.length < 2} onClick={start}>{busy ? "Starting…" : <><Play className="h-4 w-4" /> Start jury analysis</>}</Button>
    </div>
  );
}

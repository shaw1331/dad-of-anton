"use client";

import type { JuryCandidate, JuryVerdict } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function stripRefs(text: string): string {
  return text.replace(/\s*\[[A-Z0-9_]+\.(?:REPORT|CONVICTION)\.[^\]]*\]/g, "").trim();
}

function stripListRefs(items: string[]): string[] {
  return items.map(stripRefs);
}

function ratingVariant(rating: JuryCandidate["rating"]) {
  if (rating === "BUY_NOW") return "success" as const;
  if (rating === "STAGED_ENTRY") return "info" as const;
  if (rating === "SELL" || rating === "AVOID") return "destructive" as const;
  return "warning" as const;
}

function CandidateCard({ candidate }: { candidate: JuryCandidate }) {
  const c = { ...candidate };
  c.summary = stripRefs(c.summary);
  c.supporting_evidence = stripListRefs(c.supporting_evidence);
  c.counter_evidence = stripListRefs(c.counter_evidence);
  c.catalysts = stripListRefs(c.catalysts);
  c.key_risks = stripListRefs(c.key_risks);
  c.better_than = stripListRefs(c.better_than);
  c.lost_to = stripListRefs(c.lost_to);
  c.entry_conditions = stripListRefs(c.entry_conditions);
  c.invalidation_conditions = stripListRefs(c.invalidation_conditions);
  c.profit_taking_conditions = stripListRefs(c.profit_taking_conditions);
  c.reconsideration_conditions = stripListRefs(c.reconsideration_conditions);
  c.comparative_advantages = stripListRefs(c.comparative_advantages);
  c.comparative_disadvantages = stripListRefs(c.comparative_disadvantages);
  c.underperformance_scenario = stripRefs(c.underperformance_scenario);
  c.success_scenario = stripRefs(c.success_scenario);
  c.data_quality_warnings = stripListRefs(c.data_quality_warnings);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-base">{c.rank ? `#${c.rank} ` : ""}{c.ticker}</CardTitle>
          <Badge variant={ratingVariant(c.rating)}>{c.rating}</Badge>
          <Badge variant="muted">{c.portfolio_status}</Badge>
          <span className="ml-auto text-sm text-muted-foreground">{Math.round(c.conviction * 100)}% conviction</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <p className="text-foreground">{c.summary}</p>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <h4 className="font-medium text-foreground">Why this rating</h4>
            <ul className="mt-1 list-disc space-y-1 pl-4 text-muted-foreground">
              {c.supporting_evidence.map((item, i) => <li key={`support-${i}`}>{item}</li>)}
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-foreground">Counterevidence</h4>
            <ul className="mt-1 list-disc space-y-1 pl-4 text-muted-foreground">
              {c.counter_evidence.map((item, i) => <li key={`counter-${i}`}>{item}</li>)}
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-foreground">Why it wins or loses</h4>
            <p className="mt-1 text-muted-foreground">
              {c.comparative_advantages.concat(c.comparative_disadvantages).join(" ") || "No comparative explanation supplied."}
            </p>
          </div>
          <div>
            <h4 className="font-medium text-foreground">Why it may underperform</h4>
            <p className="mt-1 text-muted-foreground">{c.underperformance_scenario || "No underperformance scenario supplied."}</p>
          </div>
        </div>
        <div className="grid gap-3 border-t border-border pt-3 md:grid-cols-3">
          <div>
            <h4 className="font-medium text-foreground">Catalysts</h4>
            <p className="text-muted-foreground">{c.catalysts.join(" ") || "None identified."}</p>
          </div>
          <div>
            <h4 className="font-medium text-foreground">Risks</h4>
            <p className="text-muted-foreground">{c.key_risks.join(" ") || "None identified."}</p>
          </div>
          <div>
            <h4 className="font-medium text-foreground">Compared with</h4>
            <p className="text-muted-foreground">
              {c.better_than.length > 0 && `Better than: ${c.better_than.join(" ")}`}
              {c.lost_to.length > 0 && `${c.lost_to.join(" ")}`}
              {!c.better_than.length && !c.lost_to.length && "No comparisons supplied."}
            </p>
          </div>
        </div>
        {c.data_quality_warnings.length > 0 && (
          <div className="rounded bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-400">
            Data warnings: {c.data_quality_warnings.join(" ")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function StockJuryReport({ verdict }: { verdict: JuryVerdict }) {
  const isProgress = !verdict.schema_version && verdict.candidate_runs;
  if (isProgress) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-base">Analyzing selected stocks</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {verdict.candidate_runs?.map((candidate) => (
            <div key={candidate.ticker} className="flex justify-between rounded bg-muted/50 px-3 py-2 text-sm">
              <span>{candidate.ticker}</span>
              <Badge variant={candidate.status === "completed" ? "success" : candidate.status === "failed" ? "destructive" : "warning"}>{candidate.status}</Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }
  if (!verdict.schema_version || !Array.isArray(verdict.candidates)) return null;

  const marketView = stripRefs(verdict.market_view);
  const portfolioReasoning = stripRefs(verdict.portfolio_reasoning);
  const concentrationRisks = stripListRefs(verdict.concentration_risks);
  const dataQualityWarnings = stripListRefs(verdict.data_quality_warnings);

  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="space-y-3 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-xl font-bold text-foreground">Jury verdict</h2>
            <Badge variant={verdict.decision === "ACTIONABLE" ? "success" : "warning"}>{verdict.decision}</Badge>
            {verdict.prompt_version && <Badge variant="muted">{verdict.prompt_version}</Badge>}
          </div>
          <p className="text-sm text-foreground">{marketView}</p>
          <p className="text-sm text-muted-foreground">{portfolioReasoning}</p>
          <p className="text-sm font-medium text-foreground">Cash allocation: {verdict.cash_allocation_pct}%</p>
        </CardContent>
      </Card>
      <div className="space-y-3">
        {verdict.candidates.map((candidate) => (
          <CandidateCard key={candidate.ticker} candidate={candidate} />
        ))}
      </div>
      {(concentrationRisks.length > 0 || dataQualityWarnings.length > 0) && (
        <Card>
          <CardHeader><CardTitle className="text-base">Warnings</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm text-muted-foreground">
            {concentrationRisks.concat(dataQualityWarnings).map((warning, i) => (
              <p key={i}>• {warning}</p>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

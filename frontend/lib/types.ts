export interface InputField {
  name: string;
  type: "str" | "int" | "float" | "bool" | "text" | "ticker";
  label: string;
  description: string;
  required: boolean;
  default: any | null;
  choices?: string[] | null;
}

export interface WorkflowConfig {
  name: string;
  description: string;
  task_count: number;
  input_fields: InputField[];
}

export type TriggerType = "manual" | "scheduled" | "testing";

export interface WorkflowRun {
  id: string;
  workflow_name: string;
  status: "pending" | "running" | "completed" | "failed";
  trigger_type: TriggerType;
  current_task_index: number;
  total_tasks: number;
  created_at: string;
}

export interface TaskRun {
  task_name: string;
  task_index: number;
  status: "pending" | "running" | "completed" | "failed";
  output: Record<string, any> | null;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface RunDetail extends WorkflowRun {
  task_runs: TaskRun[];
  input: Record<string, any> | null;
  output: Record<string, any> | null;
}

export type JuryRating = "BUY_NOW" | "STAGED_ENTRY" | "WATCH" | "AVOID" | "SELL";
export type JuryPortfolioStatus = "SELECTED" | "NOT_SELECTED" | "INSUFFICIENT_DATA";

export interface JuryCandidate {
  ticker: string;
  name?: string;
  rank?: number | null;
  rating: JuryRating;
  portfolio_status: JuryPortfolioStatus;
  allocation_pct: number;
  conviction: number;
  outlook: "BULLISH" | "NEUTRAL" | "BEARISH";
  summary: string;
  supporting_evidence: string[];
  counter_evidence: string[];
  evidence_refs: string[];
  counter_evidence_refs: string[];
  catalysts: string[];
  key_risks: string[];
  success_scenario: string;
  underperformance_scenario: string;
  entry_conditions: string[];
  profit_taking_conditions: string[];
  invalidation_conditions: string[];
  reconsideration_conditions: string[];
  comparative_advantages: string[];
  comparative_disadvantages: string[];
  better_than: string[];
  lost_to: string[];
  data_quality_warnings: string[];
  trade_plan?: { entry_mode?: "IMMEDIATE" | "TRIGGERED" | "NONE"; entry_low?: number | null; entry_high?: number | null; trigger_expiry_sessions?: number | null; stop_price?: number | null; profit_targets?: number[]; max_holding_sessions?: number; expected_return_direction?: string };
}

export interface JuryVerdict {
  schema_version: string;
  decision: "ACTIONABLE" | "NO_ACTION";
  market_view: string;
  portfolio_reasoning: string;
  candidates: JuryCandidate[];
  selected: JuryCandidate[];
  rejected: JuryCandidate[];
  cash_allocation_pct: number;
  concentration_risks: string[];
  data_quality_warnings: string[];
  prompt_version?: string;
  jury_audit?: { successful_ballots?: string[]; challenges?: string[]; failures?: { agent: string; error: string }[] };
  candidate_runs?: { ticker: string; status: string; run_id?: string; error?: string }[];
}

export interface EvaluationSummary {
  status: "ready" | "not_loaded";
  required_cases: number;
  dataset: string;
  metrics?: Record<string, number | null | Record<string, number | null>>;
  release_gate?: { passed: boolean; checks: Record<string, boolean> };
}

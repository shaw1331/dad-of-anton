"use client";

import type { WorkflowRun, TriggerType } from "@/lib/types";

function StatusBadge({ status }: { status: string }) {
  const classes =
    status === "completed"
      ? "badge-success"
      : status === "failed"
        ? "badge-danger"
        : status === "running"
          ? "badge-warning"
          : "badge-muted";

  return <span className={classes}>{status}</span>;
}

function TriggerTypeBadge({ triggerType }: { triggerType: TriggerType }) {
  const classes =
    triggerType === "scheduled"
      ? "badge-purple"
      : triggerType === "testing"
        ? "badge-orange"
        : "badge-info";

  return <span className={classes}>{triggerType}</span>;
}

export function WorkflowRunList({
  runs,
  onSelect,
  onDelete,
  deletingId,
}: {
  runs: WorkflowRun[];
  onSelect: (runId: string) => void;
  onDelete?: (runId: string) => void;
  deletingId?: string | null;
}) {
  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-dark-text">Recent Runs</h2>
      {runs.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-12 text-center">
          <svg
            className="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm text-slate-500 dark:text-dark-muted">No runs yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <div
              key={run.id}
              className="card flex items-center justify-between transition-all hover:shadow-md"
            >
              <button
                onClick={() => onSelect(run.id)}
                className="flex flex-1 items-center gap-3 text-left"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
                  <svg
                    className="h-4 w-4 text-slate-600 dark:text-dark-muted"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900 dark:text-dark-text">
                    {run.workflow_name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-dark-muted">
                    {new Date(run.created_at).toLocaleString()}
                  </p>
                </div>
              </button>
              <div className="flex items-center gap-2 pr-1">
                <TriggerTypeBadge triggerType={run.trigger_type} />
                <StatusBadge status={run.status} />
                {onDelete && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(run.id);
                    }}
                    disabled={run.status === "running" || deletingId === run.id}
                    title={run.status === "running" ? "Cannot delete a running workflow" : "Delete this run"}
                    className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40 dark:text-dark-muted dark:hover:bg-red-900/30 dark:hover:text-red-400"
                  >
                    {deletingId === run.id ? (
                      <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import type { WorkflowRun } from "@/lib/types";

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

export function WorkflowRunList({
  runs,
  onSelect,
}: {
  runs: WorkflowRun[];
  onSelect: (runId: string) => void;
}) {
  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-slate-900">Recent Runs</h2>
      {runs.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-12 text-center">
          <svg
            className="mb-3 h-10 w-10 text-slate-300"
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
          <p className="text-sm text-slate-500">No runs yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <button
              key={run.id}
              onClick={() => onSelect(run.id)}
              className="card w-full text-left transition-all hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100">
                    <svg
                      className="h-4 w-4 text-slate-600"
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
                    <p className="text-sm font-medium text-slate-900">
                      {run.workflow_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {new Date(run.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <StatusBadge status={run.status} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

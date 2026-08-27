"use client";

import type { RunDetail } from "@/lib/types";

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

function ProgressBar({
  current,
  total,
  status,
}: {
  current: number;
  total: number;
  status: string;
}) {
  const pct = Math.round(((current + 1) / total) * 100);

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-3xl font-bold text-slate-900">
          {current + 1}/{total}
        </span>
        <span className="text-sm text-slate-500">{pct}% complete</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            status === "completed"
              ? "bg-emerald-500"
              : status === "failed"
                ? "bg-red-500"
                : "bg-blue-600"
          }`}
          style={{
            width: status === "completed" ? "100%" : `${pct}%`,
          }}
        />
      </div>
    </div>
  );
}

export function WorkflowRunDetail({ run }: { run: RunDetail }) {
  const hasInput = run.input && Object.keys(run.input).length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-900">
          {run.workflow_name}
        </h1>
        <StatusBadge status={run.status} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500">Progress</h3>
          <ProgressBar
            current={run.current_task_index}
            total={run.total_tasks}
            status={run.status}
          />
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500">Started</h3>
          <p className="text-sm text-slate-700">
            {new Date(run.created_at).toLocaleString()}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Run ID: {run.id.slice(0, 8)}
          </p>
        </div>
      </div>

      {hasInput && (
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500">Input</h3>
          <dl className="space-y-1">
            {Object.entries(run.input!).map(([key, value]) => (
              <div key={key} className="flex gap-2 text-sm">
                <dt className="font-medium text-slate-700">{key}:</dt>
                <dd className="text-slate-500">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Tasks</h2>
        <div className="space-y-3">
          {run.task_runs.map((task) => (
            <div
              key={task.task_index}
              className={`card ${
                task.status === "running"
                  ? "border-amber-200 bg-amber-50/50"
                  : task.status === "completed"
                    ? "border-emerald-200"
                    : task.status === "failed"
                      ? "border-red-200"
                      : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      task.status === "completed"
                        ? "bg-emerald-100 text-emerald-700"
                        : task.status === "failed"
                          ? "bg-red-100 text-red-700"
                          : task.status === "running"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {task.task_index + 1}
                  </div>
                  <span className="text-sm font-medium text-slate-900">
                    {task.task_name}
                  </span>
                </div>
                <StatusBadge status={task.status} />
              </div>

              <div className="mt-2 ml-10 space-y-1">
                {task.started_at && (
                  <p className="text-xs text-slate-500">
                    Started: {new Date(task.started_at).toLocaleString()}
                  </p>
                )}
                {task.completed_at && (
                  <p className="text-xs text-slate-500">
                    Completed: {new Date(task.completed_at).toLocaleString()}
                  </p>
                )}
                {task.error && (
                  <p className="rounded bg-red-50 px-2 py-1 text-xs text-red-600">
                    {task.error}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

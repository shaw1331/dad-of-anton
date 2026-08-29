"use client";

import { useState } from "react";
import type { RunDetail, TaskRun } from "@/lib/types";

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
        <span className="text-3xl font-bold text-slate-900 dark:text-dark-text">
          {current + 1}/{total}
        </span>
        <span className="text-sm text-slate-500 dark:text-dark-muted">{pct}% complete</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
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

function OutputModal({
  task,
  onClose,
}: {
  task: TaskRun;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 flex max-h-[80vh] w-full max-w-2xl flex-col rounded-xl bg-white p-6 shadow-xl dark:bg-dark-surface">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-dark-text">
            {task.task_name} — Output
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:text-dark-muted dark:hover:text-dark-text"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <pre className="flex-1 overflow-auto rounded-lg bg-slate-100 p-4 text-sm text-slate-800 dark:bg-slate-800 dark:text-dark-text">
          {JSON.stringify(task.output, null, 2)}
        </pre>
        <div className="mt-4 flex justify-end">
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export function WorkflowRunDetail({ run }: { run: RunDetail }) {
  const [outputModal, setOutputModal] = useState<TaskRun | null>(null);
  const hasInput = run.input && Object.keys(run.input).length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-dark-text">
          {run.workflow_name}
        </h1>
        <StatusBadge status={run.status} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500 dark:text-dark-muted">Progress</h3>
          <ProgressBar
            current={run.current_task_index}
            total={run.total_tasks}
            status={run.status}
          />
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500 dark:text-dark-muted">Started</h3>
          <p className="text-sm text-slate-700 dark:text-dark-text">
            {new Date(run.created_at).toLocaleString()}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-dark-muted">
            Run ID: {run.id.slice(0, 8)}
          </p>
        </div>
      </div>

      {hasInput && (
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500 dark:text-dark-muted">Input</h3>
          <dl className="space-y-1">
            {Object.entries(run.input!).map(([key, value]) => (
              <div key={key} className="flex gap-2 text-sm">
                <dt className="font-medium text-slate-700 dark:text-dark-text">{key}:</dt>
                <dd className="text-slate-500 dark:text-dark-muted">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-dark-text">Tasks</h2>
        <div className="space-y-3">
          {run.task_runs.map((task) => (
            <div
              key={task.task_index}
              className={`card ${
                task.status === "running"
                  ? "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-900/20"
                  : task.status === "completed"
                    ? "border-emerald-200 dark:border-emerald-800"
                    : task.status === "failed"
                      ? "border-red-200 dark:border-red-800"
                      : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      task.status === "completed"
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                        : task.status === "failed"
                          ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                          : task.status === "running"
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                            : "bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-dark-muted"
                    }`}
                  >
                    {task.task_index + 1}
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-dark-text">
                    {task.task_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {task.output && (
                    <button
                      onClick={() => setOutputModal(task)}
                      className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      Output
                    </button>
                  )}
                  <StatusBadge status={task.status} />
                </div>
              </div>

              <div className="mt-2 ml-10 space-y-1">
                {task.started_at && (
                  <p className="text-xs text-slate-500 dark:text-dark-muted">
                    Started: {new Date(task.started_at).toLocaleString()}
                  </p>
                )}
                {task.completed_at && (
                  <p className="text-xs text-slate-500 dark:text-dark-muted">
                    Completed: {new Date(task.completed_at).toLocaleString()}
                  </p>
                )}
                {task.error && (
                  <p className="rounded bg-red-50 px-2 py-1 text-xs text-red-600 dark:bg-red-900/30 dark:text-red-400">
                    {task.error}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {outputModal && (
        <OutputModal task={outputModal} onClose={() => setOutputModal(null)} />
      )}
    </div>
  );
}

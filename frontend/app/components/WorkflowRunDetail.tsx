"use client";

import { useState, useEffect } from "react";
import type { RunDetail, TaskRun, TriggerType } from "@/lib/types";

function StatusBadge({ status }: { status: string }) {
  const classes =
    status === "completed"
      ? "badge badge-success"
      : status === "failed"
        ? "badge badge-danger"
        : status === "running"
          ? "badge badge-warning"
          : "badge badge-muted";

  return <span className={classes}>{status}</span>;
}

function TriggerTypeBadge({ triggerType }: { triggerType: TriggerType }) {
  const classes =
    triggerType === "scheduled"
      ? "badge badge-purple"
      : triggerType === "testing"
        ? "badge badge-orange"
        : "badge badge-info";

  return <span className={classes}>{triggerType}</span>;
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
        <span className="text-3xl font-bold text-slate-900 dark:text-[#EDEDED]">
          {current + 1}/{total}
        </span>
        <span className="text-sm text-slate-500 dark:text-[#888888]">{pct}% complete</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-[#111111]">
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
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="mx-4 flex max-h-[80vh] w-full max-w-2xl flex-col rounded-xl bg-white p-6 shadow-xl dark:bg-[#111111]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-[#EDEDED]">
            {task.task_name} — Output
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:text-[#888888] dark:hover:text-[#EDEDED]"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <pre className="flex-1 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-100 p-4 text-sm text-slate-800 dark:bg-[#0a0a0a] dark:text-[#EDEDED]">
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

export function WorkflowRunDetail({
  run,
  onDelete,
  deleting,
}: {
  run: RunDetail;
  onDelete?: () => void;
  deleting?: boolean;
}) {
  const [outputModal, setOutputModal] = useState<TaskRun | null>(null);
  const hasInput = run.input && Object.keys(run.input).length > 0;
  const canDelete = run.status !== "running";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-[#EDEDED]">
          {run.workflow_name}
        </h1>
        <TriggerTypeBadge triggerType={run.trigger_type} />
        <StatusBadge status={run.status} />
        <div className="ml-auto">
          <button
            onClick={onDelete}
            disabled={!canDelete || deleting}
            title={canDelete ? "Delete this run" : "Cannot delete a running workflow"}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-red-600 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-[rgba(255,255,255,0.08)] dark:bg-[#111111] dark:text-red-400 dark:hover:bg-red-500/10"
          >
            {deleting ? (
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            )}
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500 dark:text-[#888888]">Progress</h3>
          <ProgressBar
            current={run.current_task_index}
            total={run.total_tasks}
            status={run.status}
          />
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500 dark:text-[#888888]">Started</h3>
          <p className="text-sm text-slate-700 dark:text-[#EDEDED]">
            {new Date(run.created_at).toLocaleString()}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-[#888888]">
            Run ID: {run.id.slice(0, 8)}
          </p>
        </div>
      </div>

      {hasInput && (
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-slate-500 dark:text-[#888888]">Input</h3>
          <dl className="space-y-1">
            {Object.entries(run.input!).map(([key, value]) => (
              <div key={key} className="flex gap-2 text-sm">
                <dt className="font-medium text-slate-700 dark:text-[#EDEDED]">{key}:</dt>
                <dd className="text-slate-500 dark:text-[#888888]">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-[#EDEDED]">Tasks</h2>
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
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400"
                        : task.status === "failed"
                          ? "bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400"
                          : task.status === "running"
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400"
                            : "bg-slate-100 text-slate-500 dark:bg-[#111111] dark:text-[#888888]"
                    }`}
                  >
                    {task.task_index + 1}
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-[#EDEDED]">
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
                  <p className="text-xs text-slate-500 dark:text-[#888888]">
                    Started: {new Date(task.started_at).toLocaleString()}
                  </p>
                )}
                {task.completed_at && (
                  <p className="text-xs text-slate-500 dark:text-[#888888]">
                    Completed: {new Date(task.completed_at).toLocaleString()}
                  </p>
                )}
                {task.error && (
                  <p className="rounded bg-red-50 px-2 py-1 text-xs text-red-600 dark:bg-red-500/10 dark:text-red-400">
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

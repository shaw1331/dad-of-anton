"use client";

import { useState, useEffect } from "react";
import type { RunDetail, TaskRun, TriggerType } from "@/lib/types";
import { Trash2, X, FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "completed"
      ? "success"
      : status === "failed"
        ? "destructive"
        : status === "running"
          ? "warning"
          : "muted";

  return <Badge variant={variant}>{status}</Badge>;
}

function TriggerTypeBadge({ triggerType }: { triggerType: TriggerType }) {
  const variant =
    triggerType === "scheduled"
      ? "purple"
      : triggerType === "testing"
        ? "orange"
        : "info";

  return <Badge variant={variant}>{triggerType}</Badge>;
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
        <span className="text-3xl font-bold text-foreground">
          {current + 1}/{total}
        </span>
        <span className="text-sm text-muted-foreground">{pct}% complete</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            status === "completed"
              ? "bg-emerald-500"
              : status === "failed"
                ? "bg-destructive"
                : "bg-primary"
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
  open,
  onClose,
}: {
  task: TaskRun;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{task.task_name} — Output</DialogTitle>
        </DialogHeader>
        <pre className="flex-1 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-muted p-4 text-sm font-mono text-foreground">
          {JSON.stringify(task.output, null, 2)}
        </pre>
        <DialogFooter>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
        <h1 className="text-2xl font-bold text-foreground">
          {run.workflow_name}
        </h1>
        <TriggerTypeBadge triggerType={run.trigger_type} />
        <StatusBadge status={run.status} />
        <div className="ml-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={onDelete}
            disabled={!canDelete || deleting}
            title={canDelete ? "Delete this run" : "Cannot delete a running workflow"}
            className="text-destructive hover:bg-destructive hover:text-destructive-foreground"
          >
            {deleting ? <Spinner size="sm" /> : <Trash2 className="h-4 w-4" />}
            Delete
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <ProgressBar
              current={run.current_task_index}
              total={run.total_tasks}
              status={run.status}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Started</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground">
              {new Date(run.created_at).toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Run ID: {run.id.slice(0, 8)}
            </p>
          </CardContent>
        </Card>
      </div>

      {hasInput && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Input</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-1">
              {Object.entries(run.input!).map(([key, value]) => (
                <div key={key} className="flex gap-2 text-sm">
                  <dt className="font-medium text-foreground">{key}:</dt>
                  <dd className="text-muted-foreground">{String(value)}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Tasks</h2>
        <div className="space-y-3">
          {run.task_runs.map((task) => (
            <Card
              key={task.task_index}
              className={
                task.status === "running"
                  ? "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-900/20"
                  : task.status === "completed"
                    ? "border-emerald-200 dark:border-emerald-800"
                    : task.status === "failed"
                      ? "border-red-200 dark:border-red-800"
                      : ""
              }
            >
              <CardContent className="p-4">
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
                              : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {task.task_index + 1}
                    </div>
                    <span className="text-sm font-medium text-foreground">
                      {task.task_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.output && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setOutputModal(task)}
                        className="h-7 gap-1 text-xs"
                      >
                        <FileText className="h-3 w-3" />
                        Output
                      </Button>
                    )}
                    <StatusBadge status={task.status} />
                  </div>
                </div>

                <div className="mt-2 ml-10 space-y-1">
                  {task.started_at && (
                    <p className="text-xs text-muted-foreground">
                      Started: {new Date(task.started_at).toLocaleString()}
                    </p>
                  )}
                  {task.completed_at && (
                    <p className="text-xs text-muted-foreground">
                      Completed: {new Date(task.completed_at).toLocaleString()}
                    </p>
                  )}
                  {task.error && (
                    <p className="rounded bg-destructive/10 px-2 py-1 text-xs text-destructive">
                      {task.error}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {outputModal && (
        <OutputModal task={outputModal} open={true} onClose={() => setOutputModal(null)} />
      )}
    </div>
  );
}

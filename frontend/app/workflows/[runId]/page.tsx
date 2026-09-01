"use client";

import { useEffect, useState, use, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import { WorkflowRunDetail } from "@/app/components/WorkflowRunDetail";
import { getWorkflowRun, deleteWorkflowRun } from "@/lib/api/workflows";
import type { RunDetail } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

export default function WorkflowRunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = use(params);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleDelete = useCallback(async () => {
    setDeleting(true);
    try {
      await deleteWorkflowRun(runId);
      window.location.href = "/workflows";
    } catch (err: any) {
      setError(err.message || "Failed to delete run");
      setDeleting(false);
    }
  }, [runId]);

  useEffect(() => {
    async function fetchRun() {
      try {
        const data = await getWorkflowRun(runId);
        setRun(data);
      } catch {
        setError("Failed to load run");
      }
    }
    fetchRun();
  }, [runId]);

  useEffect(() => {
    if (!run || run.status === "completed" || run.status === "failed") return;
    const interval = setInterval(() => {
      getWorkflowRun(runId)
        .then((data) => setRun(data))
        .catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [runId, run?.status]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <Card className="w-full max-w-sm">
          <CardContent className="flex flex-col items-center gap-4 p-6">
            <AlertTriangle className="h-10 w-10 text-destructive" />
            <p className="text-sm text-muted-foreground">{error}</p>
            <Link
              href="/workflows"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to workflows
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card className="h-32"><CardContent className="p-0"><Skeleton className="h-full" /></CardContent></Card>
          <Card className="h-32"><CardContent className="p-0"><Skeleton className="h-full" /></CardContent></Card>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="h-20"><CardContent className="p-0"><Skeleton className="h-full" /></CardContent></Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href="/workflows"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to workflows
      </Link>
      <WorkflowRunDetail run={run} onDelete={() => setShowDeleteDialog(true)} deleting={deleting} />
      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete workflow run?"
        description="This action cannot be undone. The run and all its data will be permanently removed."
        confirmLabel="Delete"
        onConfirm={handleDelete}
      />
    </div>
  );
}

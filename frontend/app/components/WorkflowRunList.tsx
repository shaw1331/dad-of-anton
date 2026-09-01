"use client";

import type { WorkflowRun, TriggerType } from "@/lib/types";
import { Play, Clock, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

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
      <h2 className="mb-4 text-lg font-semibold text-foreground">Recent Runs</h2>
      {runs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Clock className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">No runs yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <Card key={run.id} className="transition-all hover:shadow-md">
              <CardContent className="flex items-center justify-between p-4">
                <button
                  onClick={() => onSelect(run.id)}
                  className="flex flex-1 items-center gap-3 text-left"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                    <Play className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {run.workflow_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(run.created_at).toLocaleString()}
                    </p>
                  </div>
                </button>
                <div className="flex items-center gap-2 pr-1">
                  <TriggerTypeBadge triggerType={run.trigger_type} />
                  <StatusBadge status={run.status} />
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(run.id);
                      }}
                      disabled={run.status === "running" || deletingId === run.id}
                      title={run.status === "running" ? "Cannot delete a running workflow" : "Delete this run"}
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    >
                      {deletingId === run.id ? (
                        <Spinner size="sm" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState, useCallback } from "react";
import { Play, LayoutDashboard } from "lucide-react";
import { WorkflowRunList } from "@/app/components/WorkflowRunList";
import { getWorkflows, getWorkflowRuns, triggerWorkflow, deleteWorkflowRun } from "@/lib/api/workflows";
import type { WorkflowConfig, WorkflowRun, InputField } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Spinner } from "@/components/ui/spinner";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowConfig | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteRunId, setDeleteRunId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [wfData, runsData] = await Promise.all([
          getWorkflows(),
          getWorkflowRuns(),
        ]);
        setWorkflows(wfData);
        setRuns(runsData);
      } catch (err: any) {
        setError(err.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleTriggerClick = (wf: WorkflowConfig) => {
    if (wf.input_fields.length === 0) {
      handleTrigger(wf.name);
    } else {
      const defaults: Record<string, any> = {};
      for (const f of wf.input_fields) {
        defaults[f.name] = f.default ?? (f.type === "bool" ? false : "");
      }
      setFormData(defaults);
      setSelectedWorkflow(wf);
      setShowModal(true);
    }
  };

  const handleTrigger = async (workflowName: string, input?: Record<string, any>) => {
    setTriggering(workflowName);
    setShowModal(false);
    const data = await triggerWorkflow(workflowName, input);
    if (data.run_id) {
      window.location.href = `/workflows/${data.run_id}`;
    } else {
      setTriggering(null);
    }
  };

  const handleModalSubmit = () => {
    if (!selectedWorkflow) return;
    for (const f of selectedWorkflow.input_fields) {
      if (f.required && (formData[f.name] === "" || formData[f.name] === undefined || formData[f.name] === null)) {
        alert(`Missing required field: ${f.label}`);
        return;
      }
    }
    const cleaned: Record<string, any> = {};
    for (const f of selectedWorkflow.input_fields) {
      const val = formData[f.name];
      if (val === "" || val === undefined || val === null) continue;
      cleaned[f.name] = val;
    }
    handleTrigger(selectedWorkflow.name, cleaned);
  };

  const handleModalCancel = useCallback(() => {
    setShowModal(false);
    setSelectedWorkflow(null);
    setFormData({});
  }, []);

  const handleDelete = useCallback(async (runId: string) => {
    setDeletingId(runId);
    try {
      await deleteWorkflowRun(runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
    } catch (err: any) {
      setError(err.message || "Failed to delete run");
    } finally {
      setDeletingId(null);
    }
  }, []);

  const renderInputField = (field: InputField) => {
    const value = formData[field.name] ?? field.default ?? "";

    if (field.choices && field.choices.length > 0) {
      return (
        <Select
          value={String(value)}
          onValueChange={(v) => setFormData({ ...formData, [field.name]: v })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select..." />
          </SelectTrigger>
          <SelectContent>
            {field.choices.map((c) => (
              <SelectItem key={c} value={c}>
                {c.charAt(0).toUpperCase() + c.slice(1).replace(/_/g, " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    switch (field.type) {
      case "bool":
        return (
          <div className="flex items-center gap-2">
            <Checkbox
              checked={!!value}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, [field.name]: !!checked })
              }
            />
            <Label className="font-normal">{field.label}</Label>
          </div>
        );
      case "int":
        return (
          <Input
            type="number"
            step="1"
            min="1"
            value={value}
            placeholder={field.required ? "" : "Leave empty for all"}
            onChange={(e) =>
              setFormData({
                ...formData,
                [field.name]: e.target.value === "" ? "" : Number(e.target.value),
              })
            }
          />
        );
      case "float":
        return (
          <Input
            type="number"
            step="0.01"
            value={value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
          />
        );
      case "text":
        return (
          <Textarea
            value={value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
            rows={3}
          />
        );
      default:
        return (
          <Input
            type="text"
            value={value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
          />
        );
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Workflows</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Trigger and monitor your workflows
        </p>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Available Workflows
        </h2>
        {error && (
          <Card className="mb-4 border-destructive bg-destructive/10">
            <CardContent className="p-4">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}
        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <Skeleton className="mb-3 h-5 w-24" />
                  <Skeleton className="mb-4 h-4 w-full" />
                  <Skeleton className="h-9 w-24" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : workflows.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <LayoutDashboard className="mb-3 h-10 w-10 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">No workflows found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflows.map((wf) => (
              <Card key={wf.name} className="group flex flex-col transition-all hover:shadow-md">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                      <LayoutDashboard className="h-4 w-4" />
                    </div>
                    <CardTitle className="text-base">{wf.name}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-4">
                  <p className="text-sm text-muted-foreground">
                    {wf.description}
                  </p>
                  <div className="mt-auto pt-2">
                    <Button
                      onClick={() => handleTriggerClick(wf)}
                      disabled={triggering === wf.name}
                      className="w-full"
                    >
                      {triggering === wf.name ? (
                        <>
                          <Spinner size="sm" className="text-primary-foreground" />
                          Triggering...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          Trigger
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <WorkflowRunList
        runs={runs}
        onSelect={(runId) => (window.location.href = `/workflows/${runId}`)}
        onDelete={(runId) => setDeleteRunId(runId)}
        deletingId={deletingId}
      />

      <Dialog open={showModal} onOpenChange={(v) => !v && handleModalCancel()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Trigger {selectedWorkflow?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedWorkflow?.input_fields.map((field) => (
              <div key={field.name}>
                {field.type !== "bool" ? (
                  <>
                    <Label className="mb-1.5">
                      {field.label}
                      {field.required && <span className="ml-1 text-destructive">*</span>}
                    </Label>
                    {field.description && (
                      <p className="mb-1.5 text-xs text-muted-foreground">{field.description}</p>
                    )}
                    {renderInputField(field)}
                  </>
                ) : (
                  renderInputField(field)
                )}
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={handleModalCancel}>
              Cancel
            </Button>
            <Button
              onClick={handleModalSubmit}
              disabled={triggering !== null}
            >
              {triggering !== null ? (
                <>
                  <Spinner size="sm" className="text-primary-foreground" />
                  Triggering...
                </>
              ) : (
                "Trigger"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={deleteRunId !== null}
        onOpenChange={(open) => { if (!open) setDeleteRunId(null); }}
        title="Delete workflow run?"
        description="This action cannot be undone. The run and all its data will be permanently removed."
        confirmLabel="Delete"
        onConfirm={() => {
          if (deleteRunId) handleDelete(deleteRunId);
          setDeleteRunId(null);
        }}
      />
    </div>
  );
}

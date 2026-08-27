import { request } from "./client";
import type { WorkflowConfig, WorkflowRun, RunDetail } from "../types";

export async function getWorkflows(): Promise<WorkflowConfig[]> {
  return request("/workflows");
}

export async function triggerWorkflow(
  workflowName: string
): Promise<{ run_id: string }> {
  return request(`/workflows/${workflowName}/trigger`, { method: "POST" });
}

export async function getWorkflowRuns(): Promise<WorkflowRun[]> {
  return request("/workflows/runs");
}

export async function getWorkflowRun(runId: string): Promise<RunDetail> {
  return request(`/workflows/runs/${runId}`);
}

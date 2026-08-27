export interface WorkflowConfig {
  name: string;
  description: string;
  task_count: number;
}

export interface WorkflowRun {
  id: string;
  workflow_name: string;
  status: "pending" | "running" | "completed" | "failed";
  current_task_index: number;
  total_tasks: number;
  created_at: string;
}

export interface TaskRun {
  task_name: string;
  task_index: number;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface RunDetail extends WorkflowRun {
  task_runs: TaskRun[];
}

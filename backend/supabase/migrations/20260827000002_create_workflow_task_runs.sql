-- Create workflow_task_runs table to track individual task execution within a workflow run
CREATE TABLE workflow_task_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id uuid NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    task_name text NOT NULL,
    task_index int NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    error text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Unique constraint: one task per position per workflow run
CREATE UNIQUE INDEX idx_workflow_task_runs_run_index ON workflow_task_runs(workflow_run_id, task_index);

-- Index on workflow_run_id for efficient lookups
CREATE INDEX idx_workflow_task_runs_workflow_run_id ON workflow_task_runs(workflow_run_id);

-- Enable RLS
ALTER TABLE workflow_task_runs ENABLE ROW LEVEL SECURITY;

-- RLS policies: allow all operations for now
CREATE POLICY "Allow all operations on workflow_task_runs"
    ON workflow_task_runs
    FOR ALL
    USING (true)
    WITH CHECK (true);

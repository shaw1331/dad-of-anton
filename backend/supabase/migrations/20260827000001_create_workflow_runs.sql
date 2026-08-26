-- Create workflow_runs table to track each workflow execution
CREATE TABLE workflow_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name text NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    current_task_index int NOT NULL DEFAULT 0,
    total_tasks int NOT NULL,
    error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Create index on status for filtering
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);

-- Create index on created_at for ordering
CREATE INDEX idx_workflow_runs_created_at ON workflow_runs(created_at DESC);

-- Function to auto-update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on row update
CREATE TRIGGER update_workflow_runs_updated_at
    BEFORE UPDATE ON workflow_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE workflow_runs ENABLE ROW LEVEL SECURITY;

-- RLS policies: allow all operations for now
CREATE POLICY "Allow all operations on workflow_runs"
    ON workflow_runs
    FOR ALL
    USING (true)
    WITH CHECK (true);

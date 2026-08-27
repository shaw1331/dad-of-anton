-- Add updated_at column to workflow_task_runs
ALTER TABLE workflow_task_runs ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();

-- Trigger to auto-update updated_at on row update
CREATE TRIGGER update_workflow_task_runs_updated_at
    BEFORE UPDATE ON workflow_task_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE workflow_task_runs ADD COLUMN IF NOT EXISTS output jsonb;
ALTER TABLE workflow_runs ADD COLUMN IF NOT EXISTS output jsonb;

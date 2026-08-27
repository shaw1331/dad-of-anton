ALTER TABLE workflow_runs ADD COLUMN IF NOT EXISTS input jsonb;

COMMENT ON COLUMN workflow_runs.input IS 'JSON input data provided when triggering the workflow';

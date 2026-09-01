ALTER TABLE workflow_runs
  ADD COLUMN trigger_type text NOT NULL DEFAULT 'manual';

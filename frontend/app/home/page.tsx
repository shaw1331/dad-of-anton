"use client";

import { useEffect, useState, useCallback } from "react";
import { WorkflowRunList } from "@/app/components/WorkflowRunList";
import { getWorkflows, getWorkflowRuns, triggerWorkflow } from "@/lib/api/workflows";
import type { WorkflowConfig, WorkflowRun, InputField } from "@/lib/types";

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowConfig[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowConfig | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Record<string, any>>({});

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
      window.location.href = `/home/${data.run_id}`;
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

  useEffect(() => {
    if (!showModal) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleModalCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [showModal, handleModalCancel]);

  const renderInputField = (field: InputField) => {
    const value = formData[field.name] ?? field.default ?? "";

    if (field.choices && field.choices.length > 0) {
      return (
        <select
          value={value}
          onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
          className="input-field"
        >
          {field.choices.map((c) => (
            <option key={c} value={c}>
              {c.charAt(0).toUpperCase() + c.slice(1).replace(/_/g, " ")}
            </option>
          ))}
        </select>
      );
    }

    switch (field.type) {
      case "bool":
        return (
          <input
            type="checkbox"
            checked={!!value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.checked })}
            className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 dark:border-dark-border dark:bg-dark-surface"
          />
        );
      case "int":
        return (
          <input
            type="number"
            step="1"
            min="1"
            value={value}
            placeholder={field.required ? "" : "Leave empty for all"}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value === "" ? "" : Number(e.target.value) })}
            className="input-field"
          />
        );
      case "float":
        return (
          <input
            type="number"
            step="0.01"
            value={value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
            className="input-field"
          />
        );
      case "text":
        return (
          <textarea
            value={value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
            className="input-field"
            rows={3}
          />
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
            className="input-field"
          />
        );
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-dark-text">Workflows</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-dark-muted">
          Trigger and monitor your workflows
        </p>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-dark-text">
          Available Workflows
        </h2>
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400">
            {error}
          </div>
        )}
        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="mb-3 h-5 w-24 rounded bg-slate-200 dark:bg-slate-700" />
                <div className="mb-4 h-4 w-full rounded bg-slate-100 dark:bg-slate-600" />
                <div className="h-9 w-24 rounded-lg bg-slate-100 dark:bg-slate-600" />
              </div>
            ))}
          </div>
        ) : workflows.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-12 text-center">
            <svg
              className="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
            <p className="text-sm text-slate-500 dark:text-dark-muted">No workflows found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflows.map((wf) => (
              <div key={wf.name} className="card group">
                <div className="mb-1 flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-600 group-hover:text-white dark:bg-blue-900/30 dark:group-hover:bg-blue-600">
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-dark-text">
                    {wf.name}
                  </h3>
                </div>
                <p className="mb-4 ml-10 text-sm text-slate-500 dark:text-dark-muted">
                  {wf.description}
                </p>
                <button
                  onClick={() => handleTriggerClick(wf)}
                  disabled={triggering === wf.name}
                  className="btn-primary w-full"
                >
                  {triggering === wf.name ? (
                    <>
                      <svg
                        className="h-4 w-4 animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Triggering...
                    </>
                  ) : (
                    <>
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z"
                        />
                      </svg>
                      Trigger
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <WorkflowRunList
        runs={runs}
        onSelect={(runId) => (window.location.href = `/home/${runId}`)}
      />

      {showModal && selectedWorkflow && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={handleModalCancel}
        >
          <div
            className="mx-4 w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-dark-surface"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-dark-text">
              Trigger {selectedWorkflow.name}
            </h3>
            <div className="space-y-4">
              {selectedWorkflow.input_fields.map((field) => (
                <div key={field.name}>
                  <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-dark-muted">
                    {field.label}
                    {field.required && <span className="ml-1 text-red-500">*</span>}
                  </label>
                  {field.description && (
                    <p className="mb-1 text-xs text-slate-400 dark:text-slate-500">{field.description}</p>
                  )}
                  {renderInputField(field)}
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={handleModalCancel} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleModalSubmit}
                disabled={triggering !== null}
                className="btn-primary"
              >
                {triggering !== null ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Triggering...
                  </>
                ) : (
                  "Trigger"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { WorkflowRunList } from "@/app/components/WorkflowRunList";
import { getWorkflows, getWorkflowRuns, triggerWorkflow } from "@/lib/api/workflows";

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Array<{ name: string; description: string }>>([]);
  const [runs, setRuns] = useState<Array<{ runId: string; workflowName: string; status: string; createdAt: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      const [wfData, runsData] = await Promise.all([
        getWorkflows(),
        getWorkflowRuns(),
      ]);
      setWorkflows(wfData);
      setRuns(runsData);
      setLoading(false);
    }
    fetchData();
  }, []);

  const handleTrigger = async (workflowName: string) => {
    setTriggering(workflowName);
    const data = await triggerWorkflow(workflowName);
    if (data.run_id) {
      window.location.href = `/workflows/${data.run_id}`;
    } else {
      setTriggering(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Workflows</h1>
        <p className="mt-1 text-sm text-slate-500">
          Trigger and monitor your workflows
        </p>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">
          Available Workflows
        </h2>
        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="mb-3 h-5 w-24 rounded bg-slate-200" />
                <div className="mb-4 h-4 w-full rounded bg-slate-100" />
                <div className="h-9 w-24 rounded-lg bg-slate-100" />
              </div>
            ))}
          </div>
        ) : workflows.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-12 text-center">
            <svg
              className="mb-3 h-10 w-10 text-slate-300"
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
            <p className="text-sm text-slate-500">No workflows found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflows.map((wf) => (
              <div key={wf.name} className="card group">
                <div className="mb-1 flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-600 group-hover:text-white">
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
                  <h3 className="text-base font-semibold text-slate-900">
                    {wf.name}
                  </h3>
                </div>
                <p className="mb-4 ml-10 text-sm text-slate-500">
                  {wf.description}
                </p>
                <button
                  onClick={() => handleTrigger(wf.name)}
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
        onSelect={(runId) => (window.location.href = `/workflows/${runId}`)}
      />
    </div>
  );
}

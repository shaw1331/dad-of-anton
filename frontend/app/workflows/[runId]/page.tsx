"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { WorkflowRunDetail } from "@/app/components/WorkflowRunDetail";
import { getWorkflowRun } from "@/lib/api/workflows";
import type { RunDetail } from "@/lib/types";

export default function WorkflowRunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = use(params);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRun() {
      try {
        const data = await getWorkflowRun(runId);
        setRun(data);
      } catch {
        setError("Failed to load run");
      }
    }
    fetchRun();
  }, [runId]);

  useEffect(() => {
    if (!run || run.status === "completed" || run.status === "failed") return;
    const interval = setInterval(() => {
      getWorkflowRun(runId)
        .then((data) => setRun(data))
        .catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [runId, run?.status]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <svg
          className="mb-4 h-12 w-12 text-red-300"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
          />
        </svg>
        <p className="mb-4 text-sm text-slate-600">{error}</p>
        <Link href="/workflows" className="btn-ghost">
          Back to workflows
        </Link>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="h-8 w-48 animate-pulse rounded bg-slate-200" />
          <div className="h-6 w-16 animate-pulse rounded-full bg-slate-200" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="card h-32 animate-pulse" />
          <div className="card h-32 animate-pulse" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card h-20 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href="/workflows"
        className="inline-flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-slate-900"
      >
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
            d="M15.75 19.5L8.25 12l7.5-7.5"
          />
        </svg>
        Back to workflows
      </Link>
      <WorkflowRunDetail run={run} />
    </div>
  );
}

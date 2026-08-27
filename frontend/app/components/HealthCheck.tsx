"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api/health";

export default function HealthCheck() {
  const [status, setStatus] = useState<string>("checking");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then((data) => setStatus(data.status))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-2.5 w-2.5 rounded-full ${
            error
              ? "bg-red-500"
              : status === "healthy"
                ? "bg-emerald-500"
                : "bg-amber-500 animate-pulse"
          }`}
        />
        <div>
          <p className="text-sm font-medium text-slate-900">Backend Status</p>
          <p className="text-xs text-slate-500">
            {error ? (
              <span className="text-red-600">{error}</span>
            ) : status === "checking" ? (
              "Connecting..."
            ) : (
              <span className="capitalize">{status}</span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

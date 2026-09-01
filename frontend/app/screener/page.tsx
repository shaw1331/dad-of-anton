"use client";

import { useState } from "react";
import { triggerWorkflow } from "@/lib/api/workflows";

export default function ScreenerPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError("Please enter a screener query");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await triggerWorkflow("screener_query", {
        query: trimmed,
      });
      if (data.run_id) {
        window.location.href = `/home/${data.run_id}`;
      }
    } catch (err: any) {
      setError(err.message || "Failed to trigger workflow");
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-dark-text">
          Screener
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-dark-muted">
          Find stocks matching an index or query from screener.in
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card max-w-lg">
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-dark-muted">
          Screener Query
          <span className="ml-1 text-red-500">*</span>
        </label>
        <p className="mb-2 text-xs text-slate-400 dark:text-slate-500">
          Index name or query (e.g. NIFTY50, SMALLCAP50)
        </p>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="NIFTY50"
          className="input-field"
        />
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary mt-4 w-full"
        >
          {loading ? (
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
              Searching...
            </>
          ) : (
            "Run Screener"
          )}
        </button>
      </form>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api/health";
import { Card, CardContent } from "@/components/ui/card";

export default function HealthCheck() {
  const [status, setStatus] = useState<string>("checking");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then((data) => setStatus(data.status))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-2.5 w-2.5 rounded-full ${
              error
                ? "bg-destructive"
                : status === "healthy"
                  ? "bg-emerald-500"
                  : "bg-amber-500 animate-pulse"
            }`}
          />
          <div>
            <p className="text-sm font-medium text-foreground">Backend Status</p>
            <p className="text-xs text-muted-foreground">
              {error ? (
                <span className="text-destructive">{error}</span>
              ) : status === "checking" ? (
                "Connecting..."
              ) : (
                <span className="capitalize">{status}</span>
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

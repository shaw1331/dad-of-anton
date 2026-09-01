import Link from "next/link";
import { Sparkles, LayoutDashboard } from "lucide-react";
import HealthCheck from "./components/HealthCheck";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="text-center">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg shadow-primary/25">
          <Sparkles className="h-8 w-8 text-primary-foreground" />
        </div>
        <h1 className="mb-3 text-4xl font-bold tracking-tight text-foreground">
          Dad of Anton
        </h1>
        <p className="mb-8 text-lg text-muted-foreground">
          Workflow orchestration dashboard
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link
            href="/workflows"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
          >
            <LayoutDashboard className="h-4 w-4" />
            View Workflows
          </Link>
        </div>
      </div>

      <div className="mt-16 w-full max-w-md">
        <HealthCheck />
      </div>
    </div>
  );
}

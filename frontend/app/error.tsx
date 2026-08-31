"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <p className="mb-4 text-sm text-slate-600">Something went wrong</p>
      <button onClick={reset} className="btn-primary">
        Try again
      </button>
    </div>
  );
}

import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <p className="mb-4 text-sm text-slate-600">Page not found</p>
      <Link href="/" className="btn-ghost">
        Go home
      </Link>
    </div>
  );
}

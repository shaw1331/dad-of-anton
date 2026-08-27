# DOA-008: Frontend — configurable API base URL and crash-safe Supabase env handling

- **Type:** Bug / Tech debt
- **Priority:** P1
- **Component:** frontend
- **Affected files:** `frontend/app/components/HealthCheck.tsx`, `frontend/lib/supabase.ts`, `frontend/.env.local.example`

## Problems

1. **Hardcoded backend URL.** `HealthCheck.tsx:10` fetches `http://localhost:8000/api/v1/health` — a literal. The app cannot point at any deployed backend without a code change, and it targets the v1 health duplicate being removed in DOA-007.

2. **Non-null assertions on env vars crash the whole app.** `frontend/lib/supabase.ts`:

   ```ts
   const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
   const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

   export const supabase = createClient(supabaseUrl, supabaseAnonKey);
   ```

   `!` lies to the compiler; at runtime, missing envs pass `undefined` into `createClient`, which throws **at module import** — taking down every page that transitively imports this file, with an opaque error. Fail with an explicit, named-variable error instead.

3. **No fetch error/abort handling.** The health fetch has no timeout/abort on unmount and treats any non-JSON/non-2xx response as success-path.

## Steps of completion

1. Introduce `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`); read it in a small helper and use it in `HealthCheck.tsx`, pointing at `/health` (the endpoint kept by DOA-007).
2. Replace the `!` assertions in `lib/supabase.ts` with an explicit check that throws a descriptive error naming the missing variables.
3. Handle non-OK responses and abort the fetch on unmount.
4. Document the new variable in `.env.local.example`.
5. Verify: with no `.env.local`, `npm run dev` renders the page and HealthCheck shows the backend status (defaults still point at localhost); with a bogus `NEXT_PUBLIC_API_URL`, an error message renders instead of a hung "Checking...".

## Changes (diff)

### `frontend/app/components/HealthCheck.tsx`

```diff
@@ -1,26 +1,41 @@
 "use client";

 import { useEffect, useState } from "react";

+const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
+
 export default function HealthCheck() {
   const [status, setStatus] = useState<string>("Checking...");
   const [error, setError] = useState<string | null>(null);

   useEffect(() => {
-    fetch("http://localhost:8000/api/v1/health")
-      .then((res) => res.json())
+    const controller = new AbortController();
+
+    fetch(`${API_URL}/health`, { signal: controller.signal })
+      .then((res) => {
+        if (!res.ok) {
+          throw new Error(`Backend returned ${res.status}`);
+        }
+        return res.json();
+      })
       .then((data) => setStatus(data.status))
-      .catch((err) => setError(err.message));
+      .catch((err) => {
+        if (err.name !== "AbortError") {
+          setError(err.message);
+        }
+      });
+
+    return () => controller.abort();
   }, []);

   return (
     <div>
       <h2>Backend Health</h2>
       {error ? (
         <p style={{ color: "red" }}>Error: {error}</p>
       ) : (
         <p>Status: {status}</p>
       )}
     </div>
   );
 }
```

### `frontend/lib/supabase.ts`

```diff
@@ -1,6 +1,14 @@
 import { createClient } from "@supabase/supabase-js";

-const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
-const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
+const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
+const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
+
+if (!supabaseUrl || !supabaseAnonKey) {
+  throw new Error(
+    "Missing Supabase configuration: set NEXT_PUBLIC_SUPABASE_URL and " +
+      "NEXT_PUBLIC_SUPABASE_ANON_KEY in frontend/.env.local"
+  );
+}

 export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

### `frontend/.env.local.example`

```diff
+# Base URL of the FastAPI backend (no trailing slash)
+NEXT_PUBLIC_API_URL=http://localhost:8000
 NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
 NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

*(Keep whatever variables already exist in the example file; only add the new key at the top.)*

## Acceptance criteria

- [ ] No literal `localhost:8000` remains outside the single `API_URL` fallback (`grep -rn "localhost:8000" frontend/app frontend/lib`).
- [ ] Missing Supabase envs produce an error that names both variables (not `supabaseUrl is required`-style internals).
- [ ] HealthCheck shows an error state for non-2xx responses and doesn't set state after unmount.
- [ ] Works against DOA-007's single `/health` endpoint.

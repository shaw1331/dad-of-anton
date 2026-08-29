# DOA-009: Security — lock down wide-open RLS policies; use service-role key server-side

- **Type:** Security
- **Priority:** P1
- **Component:** backend / database
- **Affected files:** new `backend/supabase/migrations/20260827000004_lock_down_rls.sql`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/.env.example`

## Problem

Both migrations enable RLS and then immediately neutralize it (`20260827000001_create_workflow_runs.sql:38-42`, `20260827000002_create_workflow_task_runs.sql:24-28`):

```sql
CREATE POLICY "Allow all operations on workflow_runs"
    ON workflow_runs
    FOR ALL
    USING (true)
    WITH CHECK (true);
```

Combined with the backend using the **anon key** (`config.py:11`, `database.py:8-9`), this means *anyone who obtains the anon key* — which is by design a publishable, client-side key (it ships in the frontend bundle via `NEXT_PUBLIC_SUPABASE_ANON_KEY`) — can read, insert, update, and **delete** every row in `workflow_runs` and `workflow_task_runs` by talking to Supabase directly, bypassing the API entirely.

## Fix

- The backend is a trusted server process → it should authenticate with the **service-role key** (bypasses RLS by design; never shipped to a browser).
- Drop the allow-all policies. With no permissive policy, RLS-enabled tables deny anon/authenticated roles by default — the frontend never queries these tables directly (verified: `frontend/lib/supabase.ts` is only used for the client, no table access in the repo today).

## Steps of completion

1. Add migration `20260827000004_lock_down_rls.sql` dropping both allow-all policies.
2. Add `SUPABASE_SERVICE_ROLE_KEY` to `Settings` and `.env.example`.
3. Prefer the service-role key in `database.py` (fall back to anon for local anon-only setups, with a warning).
4. Apply the migration (`supabase db push` or dashboard SQL editor).
5. Verify: with only the anon key, a direct PostgREST call to `/rest/v1/workflow_runs` returns an empty set / permission denial; the backend (service key) still passes all endpoint smoke tests.
6. Rotate the anon key if this deployment ever ran publicly with the allow-all policies.

## Changes (diff)

### `backend/supabase/migrations/20260827000004_lock_down_rls.sql` (new file)

```diff
@@ -0,0 +1,9 @@
+-- The backend now authenticates with the service-role key (bypasses RLS).
+-- Remove the permissive policies so the publishable anon key can no longer
+-- read or mutate workflow state directly.
+
+DROP POLICY "Allow all operations on workflow_runs" ON workflow_runs;
+DROP POLICY "Allow all operations on workflow_task_runs" ON workflow_task_runs;
+
+-- RLS remains ENABLED on both tables; with no permissive policy, anon and
+-- authenticated roles are denied by default.
```

### `backend/app/core/config.py`

```diff
@@ -8,7 +8,8 @@
     CORS_ORIGINS: List[str] = ["http://localhost:3000"]

     SUPABASE_URL: str = ""
     SUPABASE_ANON_KEY: str = ""
+    SUPABASE_SERVICE_ROLE_KEY: str = ""
```

### `backend/app/core/database.py`

*(shown against DOA-001's `get_supabase()`; if DOA-001 hasn't landed, apply the same key-selection logic to the module-level block)*

```diff
@@ -1,8 +1,10 @@
 from __future__ import annotations

+import logging
+
 from supabase import create_client, Client
 from app.core.config import settings

+logger = logging.getLogger(__name__)
+
 _client: Client | None = None


 def get_supabase() -> Client:
     global _client
     if _client is None:
-        if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
+        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
+        if not (settings.SUPABASE_URL and key):
             raise RuntimeError(
                 "Supabase is not configured: set SUPABASE_URL and "
-                "SUPABASE_ANON_KEY in backend/.env"
+                "SUPABASE_SERVICE_ROLE_KEY (preferred) or SUPABASE_ANON_KEY "
+                "in backend/.env"
             )
-        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
+        if not settings.SUPABASE_SERVICE_ROLE_KEY:
+            logger.warning(
+                "Using anon key for server-side Supabase access; workflow "
+                "tables are locked by RLS and writes will fail. Set "
+                "SUPABASE_SERVICE_ROLE_KEY."
+            )
+        _client = create_client(settings.SUPABASE_URL, key)
     return _client
```

### `backend/.env.example`

```diff
 SUPABASE_URL=https://your-project.supabase.co
 SUPABASE_ANON_KEY=your-anon-key
+# Server-side only. NEVER expose this in the frontend or commit a real value.
+SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Do / Don't (security)

- **Do** keep the service-role key exclusively in `backend/.env` (already gitignored) and in the deployment secret store.
- **Don't** ever prefix it `NEXT_PUBLIC_`, log it, or paste it in a ticket.
- **Don't** re-add permissive (`USING (true)`) policies later "to debug" — use the service key + SQL editor instead.

## Acceptance criteria

- [ ] `curl -H "apikey: <anon>" "$SUPABASE_URL/rest/v1/workflow_runs?select=*"` returns no rows / 401-style denial.
- [ ] All backend workflow endpoints still work using the service-role key.
- [ ] TruffleHog pre-commit hook passes (no real keys in the diff).

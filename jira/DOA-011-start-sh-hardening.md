# DOA-011: Harden `start.sh` — clean shutdown, fail-fast, no orphaned processes

- **Type:** Bug (dev experience)
- **Priority:** P2
- **Component:** tooling
- **Affected files:** `start.sh`

## Problem

`start.sh` (repo root):

1. **No `set -e`** — if `pip install` or `npm install` fails, the script barrels on and starts broken servers.
2. **No signal trap** — the closing message says "Press Ctrl+C to stop both servers", but Ctrl+C only interrupts `wait`; the backgrounded `uvicorn` and `npm run dev` (and its child `next dev`) frequently survive as orphans holding ports 8000/3000. The next `./start.sh` then fails with "address already in use".
3. **`cd` without failure handling** — with `set -e` absent, a missing directory leads to installing/starting in the wrong place.

## Steps of completion

1. Add `set -euo pipefail` and a `cleanup()` trap on `EXIT INT TERM` that kills both PIDs (and their children via negative PGID where available).
2. Guard the `cd`s.
3. Test: run `./start.sh`, Ctrl+C, then `lsof -i :8000 -i :3000` — no survivors; re-run starts cleanly.

## Before / after

**Before** — plain script, background jobs with `&`, single `wait $BACKEND_PID $FRONTEND_PID`, no traps.

**After** — fail-fast options, `trap`-based cleanup killing both process groups, safe `cd`s.

## Changes (diff)

### `start.sh`

```diff
@@ -1,36 +1,49 @@
 #!/bin/bash
+set -euo pipefail
+
+BACKEND_PID=""
+FRONTEND_PID=""
+
+cleanup() {
+    echo ""
+    echo "Stopping servers..."
+    # Kill each background job's process group so children (next dev,
+    # uvicorn reloader) die too. Fall back to plain kill.
+    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
+        [ -n "$pid" ] || continue
+        kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
+    done
+}
+trap cleanup EXIT INT TERM

 echo "Starting Dad of Anton applications..."

 # Setup and start backend
 echo "Setting up FastAPI backend..."
-cd backend
+cd backend || exit 1
 if [ ! -d "venv" ]; then
     echo "Creating virtual environment..."
     python3 -m venv venv
 fi
 source venv/bin/activate
 pip install -q -r requirements.txt
-uvicorn app.main:app --reload --port 8000 &
+set -m
+uvicorn app.main:app --reload --port 8000 &
 BACKEND_PID=$!
 cd ..

 # Setup and start frontend
 echo "Setting up Next.js frontend..."
-cd frontend
+cd frontend || exit 1
 if [ ! -d "node_modules" ]; then
     echo "Installing npm dependencies..."
     npm install
 fi
 npm run dev &
 FRONTEND_PID=$!
 cd ..

 echo "Both applications started!"
 echo "Backend: http://localhost:8000"
 echo "Frontend: http://localhost:3000"
 echo ""
 echo "Press Ctrl+C to stop both servers"

 # Wait for both processes
-wait $BACKEND_PID $FRONTEND_PID
+wait "$BACKEND_PID" "$FRONTEND_PID" || true
```

> `set -m` enables job control so each background job gets its own process group, making `kill -- -PGID` reach `next dev`'s children. The `|| true` on `wait` keeps `set -e` from turning a Ctrl-C (non-zero wait status) into an unclean exit before the trap runs.

## Acceptance criteria

- [ ] After Ctrl+C, `lsof -i :8000 -i :3000` shows nothing.
- [ ] A failing `pip install` aborts the script before anything starts.
- [ ] `shellcheck start.sh` reports no errors.

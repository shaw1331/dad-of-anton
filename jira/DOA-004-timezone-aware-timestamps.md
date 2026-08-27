# DOA-004: Timezone-aware timestamps in `BaseModel` (drop deprecated `datetime.utcnow`)

- **Type:** Bug / Tech debt
- **Priority:** P1
- **Component:** backend / models
- **Affected files:** `backend/app/models/base.py`

## Problem

`backend/app/models/base.py:12-13` uses `datetime.utcnow`:

```python
created_at: datetime = Field(default_factory=datetime.utcnow)
updated_at: datetime = Field(default_factory=datetime.utcnow)
```

Three issues:

1. **`datetime.utcnow()` is deprecated** (Python 3.12+) and scheduled for removal.
2. **It returns a *naive* datetime.** When serialized via `model_dump(mode="json")` it produces an ISO string with **no UTC offset** (e.g. `2026-08-27T10:15:00.123456`). The DB columns are `timestamptz` (`migrations/20260827000001`, `...0002`), so Postgres interprets the naive string in the *session* timezone. It happens to work while the session TZ is UTC, but it is silently wrong the moment that assumption breaks — and it is inconsistent with the repositories, which already write timezone-aware values (`datetime.now(timezone.utc).isoformat()`).
3. `typing.Optional` is imported at `base.py:5` and never used.

Additionally, `id` defaults to `uuid.uuid4().hex` (dash-less). Postgres accepts it for `uuid` columns, but the value read back is the canonical dashed form — so the string the API returned at trigger time (`run_id`) is not byte-equal to the `id` field returned later by `GET /runs`. Use the canonical dashed representation from the start.

## Steps of completion

1. Add a module-level `utc_now()` helper returning `datetime.now(timezone.utc)`.
2. Point both `default_factory`s at it; switch `id` to `str(uuid.uuid4())`.
3. Remove the unused `Optional` import.
4. Trigger a workflow and verify in Supabase that `created_at`/`updated_at` are stored with the intended UTC instant and that `run_id` returned by the trigger endpoint matches `id` in `GET /api/v1/workflows/runs/{run_id}` exactly.

## Before / after

**Before** — `backend/app/models/base.py` (entire file):

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**After** — timezone-aware timestamps (serialize with `+00:00` offset), canonical dashed UUIDs, no unused imports.

## Changes (diff)

### `backend/app/models/base.py`

```diff
@@ -1,13 +1,16 @@
 from __future__ import annotations

 import uuid
-from datetime import datetime
-from typing import Optional
+from datetime import datetime, timezone

 from pydantic import BaseModel as PydanticBaseModel, Field


+def utc_now() -> datetime:
+    return datetime.now(timezone.utc)
+
+
 class BaseModel(PydanticBaseModel):
-    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
-    created_at: datetime = Field(default_factory=datetime.utcnow)
-    updated_at: datetime = Field(default_factory=datetime.utcnow)
+    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
+    created_at: datetime = Field(default_factory=utc_now)
+    updated_at: datetime = Field(default_factory=utc_now)
```

## Acceptance criteria

- [ ] `model_dump(mode="json")` on a fresh `WorkflowRun` yields `created_at` ending in `+00:00` (or `Z`).
- [ ] `run_id` returned by `POST /workflows/sample/trigger` is identical to the `id` value later returned by `GET /workflows/runs/{run_id}`.
- [ ] `python -W error::DeprecationWarning -c "from app.models.base import BaseModel; BaseModel()"` raises no deprecation warning (run from `backend/`).

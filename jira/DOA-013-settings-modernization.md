# DOA-013: Modernize `Settings` — pydantic-settings v2 style, env-driven CORS

- **Type:** Tech debt
- **Priority:** P2
- **Component:** backend / core
- **Affected files:** `backend/app/core/config.py`, `backend/.env.example`

## Problem

`backend/app/core/config.py`:

1. Uses the **pydantic v1-style inner `class Config`** (`config.py:13-16`). The project pins `pydantic-settings==2.7.1`, where the supported form is `model_config = SettingsConfigDict(...)`; the v1 form is deprecated and will break on the next major bump.
2. `CORS_ORIGINS` is hardcoded to `["http://localhost:3000"]` — any deployed frontend origin requires a code change. pydantic-settings can parse a JSON list from an env var out of the box.
3. `typing.List` is legacy; the codebase elsewhere uses builtin generics (`list[...]`).

## Steps of completion

1. Replace the inner `Config` class with `model_config = SettingsConfigDict(...)`.
2. `List[str]` → `list[str]`; drop the `typing` import.
3. Document `CORS_ORIGINS` (JSON-array syntax) in `.env.example`.
4. Verify: `CORS_ORIGINS='["https://app.example.com"]' uvicorn app.main:app` responds to a preflight from that origin; default behavior unchanged when the var is unset.

## Before / after

**Before** — `backend/app/core/config.py` (entire file):

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dad of Anton API"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

**After** — v2-style config dict, builtin generics, overridable CORS.

## Changes (diff)

### `backend/app/core/config.py`

```diff
@@ -1,19 +1,19 @@
-from pydantic_settings import BaseSettings
-from typing import List
+from pydantic_settings import BaseSettings, SettingsConfigDict


 class Settings(BaseSettings):
+    model_config = SettingsConfigDict(
+        case_sensitive=True,
+        env_file=".env",
+        env_file_encoding="utf-8",
+    )
+
     PROJECT_NAME: str = "Dad of Anton API"
     API_V1_PREFIX: str = "/api/v1"
-    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
+    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

     SUPABASE_URL: str = ""
     SUPABASE_ANON_KEY: str = ""
-
-    class Config:
-        case_sensitive = True
-        env_file = ".env"
-        env_file_encoding = "utf-8"


 settings = Settings()
```

*(If DOA-009 has landed, `SUPABASE_SERVICE_ROLE_KEY: str = ""` is also present — keep it.)*

### `backend/.env.example`

```diff
 SUPABASE_URL=https://your-project.supabase.co
 SUPABASE_ANON_KEY=your-anon-key
+# Optional: JSON array of allowed browser origins (defaults to localhost:3000)
+# CORS_ORIGINS=["http://localhost:3000","https://app.example.com"]
```

## Acceptance criteria

- [ ] App boots identically with no env overrides.
- [ ] `CORS_ORIGINS` set as a JSON array in the environment is honored by the CORS middleware.
- [ ] No `class Config` / `typing.List` remains in `backend/app/core/config.py`.

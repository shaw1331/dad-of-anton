from __future__ import annotations

from supabase import create_client, Client
from app.core.config import settings

supabase: Client | None = None

if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
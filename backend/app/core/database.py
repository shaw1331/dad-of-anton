from __future__ import annotations

from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """Create a new Supabase client per request for thread safety."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

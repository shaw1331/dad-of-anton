from __future__ import annotations

from datetime import datetime, timezone

from app.core.database import get_supabase_client


class TradeRepo:
    def insert(self, row: dict) -> dict:
        supabase = get_supabase_client()
        result = supabase.table("trades").insert(row).execute()
        return result.data[0]

    def get(self, trade_id: str) -> dict | None:
        supabase = get_supabase_client()
        result = supabase.table("trades").select("*").eq("id", trade_id).execute()
        if not result.data:
            return None
        return result.data[0]

    def list_all(self) -> list[dict]:
        supabase = get_supabase_client()
        result = supabase.table("trades").select("*").order("opened_at", desc=True).execute()
        return result.data or []

    def list_open(self) -> list[dict]:
        supabase = get_supabase_client()
        result = supabase.table("trades").select("*").eq("status", "open").execute()
        return result.data or []

    def delete(self, trade_id: str) -> bool:
        supabase = get_supabase_client()
        found = supabase.table("trades").select("id").eq("id", trade_id).execute()
        if not found.data:
            return False
        supabase.table("trades").delete().eq("id", trade_id).execute()
        return True

    def update_open_price(self, ticker: str, price: float) -> None:
        supabase = get_supabase_client()
        supabase.table("trades").update({"current_price": price}).eq(
            "ticker", ticker
        ).eq("status", "open").execute()

    def close(self, trade_id: str, reason: str, exit_price: float) -> None:
        supabase = get_supabase_client()
        supabase.table("trades").update({
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "close_reason": reason,
            "exit_price": exit_price,
        }).eq("id", trade_id).execute()

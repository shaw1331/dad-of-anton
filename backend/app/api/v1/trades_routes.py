from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from app.stock_cache.cache import get_stocks
from app.trades.prices import fetch_ltp
from app.trades.qty import suggested_quantity, suggested_stop, suggested_take_profit
from app.trades.repo import TradeRepo

router = APIRouter(prefix="/trades", tags=["trades"])
repo = TradeRepo()


# --- Pydantic models (plan: no models.py, keep here) ---


class CreateTradeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    quantity: int = Field(ge=1)
    stop_loss: float = Field(gt=0, alias="stopLoss")
    take_profit: float = Field(gt=0, alias="takeProfit")
    notes: str | None = None


class CloseTradeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: Literal["manual", "tp", "sl"]
    exit_price: float = Field(gt=0, alias="exitPrice")


class PatchTradeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quantity: int | None = Field(default=None, ge=1)
    stop_loss: float | None = Field(default=None, alias="stopLoss")
    take_profit: float | None = Field(default=None, alias="takeProfit")
    notes: str | None = None


# --- Helpers ---


def resolve_name(ticker: str) -> str:
    needle = ticker.upper()
    for stock in get_stocks():
        if stock["symbol"].upper() == needle:
            return stock["name"]
    return ticker


def to_trade_json(row: dict) -> dict:
    closed = row.get("status") == "closed"
    return {
        "id": row["id"],
        "ticker": row["ticker"],
        "name": row["name"],
        "side": row["side"],
        "status": row["status"],
        "entryPrice": float(row["entry_price"]),
        "quantity": row["quantity"],
        "stopLoss": float(row["stop_loss"]) if row.get("stop_loss") is not None else None,
        "takeProfit": float(row["take_profit"]) if row.get("take_profit") is not None else None,
        "currentPrice": None if closed else (float(row["current_price"]) if row.get("current_price") is not None else None),
        "openedAt": row["opened_at"],
        "closedAt": row.get("closed_at"),
        "closeReason": row.get("close_reason"),
        "exitPrice": float(row["exit_price"]) if row.get("exit_price") is not None else None,
        "notes": row.get("notes"),
    }


# --- Routes ---


@router.get("/quote")
def get_quote(ticker: str):
    t = ticker.strip().upper()
    if not t:
        raise HTTPException(status_code=422, detail="Ticker required")
    ltp = fetch_ltp(t)
    if ltp is None:
        raise HTTPException(status_code=404, detail=f"No live price for {t}")
    return {
        "ticker": t,
        "name": resolve_name(t),
        "ltp": ltp,
        "quantity": suggested_quantity(ltp),
        "stopLoss": suggested_stop(ltp),
        "takeProfit": suggested_take_profit(ltp),
    }


@router.post("", status_code=201)
def create_trade(body: CreateTradeRequest):
    t = body.ticker.strip().upper()
    if not t:
        raise HTTPException(status_code=422, detail="Ticker required")
    ltp = fetch_ltp(t)
    if ltp is None:
        raise HTTPException(status_code=404, detail=f"No live price for {t}")
    row = repo.insert({
        "ticker": t,
        "name": resolve_name(t),
        "side": "long",
        "status": "open",
        "entry_price": ltp,
        "current_price": ltp,
        "quantity": body.quantity,
        "stop_loss": body.stop_loss,
        "take_profit": body.take_profit,
        "notes": body.notes,
    })
    return to_trade_json(row)


@router.get("")
def list_trades():
    return {"trades": [to_trade_json(r) for r in repo.list_all()]}


@router.post("/{trade_id}/close")
def close_trade(trade_id: str, body: CloseTradeRequest):
    row = repo.get(trade_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Trade not found: {trade_id}")
    if row["status"] != "open":
        raise HTTPException(status_code=409, detail="Trade already closed")
    if body.reason == "manual" and row.get("current_price") is None:
        raise HTTPException(status_code=409, detail="No current price to close at")
    exit_price = body.exit_price
    repo.close(trade_id, body.reason, exit_price)
    updated = repo.get(trade_id)
    return to_trade_json(updated)


@router.patch("/{trade_id}")
def patch_trade(trade_id: str, body: PatchTradeRequest):
    row = repo.get(trade_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Trade not found: {trade_id}")
    fields: dict = {"notes": body.notes}
    if row["status"] == "open":
        if body.quantity is not None:
            fields["quantity"] = body.quantity
        fields["stop_loss"] = body.stop_loss
        fields["take_profit"] = body.take_profit
    repo.update(trade_id, fields)
    updated = repo.get(trade_id)
    return to_trade_json(updated)


@router.delete("/{trade_id}", status_code=204)
def delete_trade(trade_id: str):
    if not repo.delete(trade_id):
        raise HTTPException(status_code=404, detail=f"Trade not found: {trade_id}")
    return Response(status_code=204)

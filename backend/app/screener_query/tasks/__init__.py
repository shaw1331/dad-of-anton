__all__ = ["QueryScreenerTask"]


def __getattr__(name: str):
    if name == "QueryScreenerTask":
        from app.screener_query.tasks.query_screener import QueryScreenerTask
        return QueryScreenerTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["QueryScreenerTask", "SCREENER_QUERY_WORKFLOW"]


def __getattr__(name: str):
    if name == "QueryScreenerTask":
        from app.screener_query.tasks.query_screener import QueryScreenerTask
        return QueryScreenerTask
    elif name == "SCREENER_QUERY_WORKFLOW":
        from app.screener_query.workflow import SCREENER_QUERY_WORKFLOW
        return SCREENER_QUERY_WORKFLOW
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

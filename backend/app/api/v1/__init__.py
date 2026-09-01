from fastapi import APIRouter

from app.api.v1.nse_screener_routes import router as nse_screener_router
from app.api.v1.tradingview_routes import router as tradingview_router
from app.api.v1.workflow_routes import router as workflow_router

api_router = APIRouter()

api_router.include_router(workflow_router)
api_router.include_router(tradingview_router)
api_router.include_router(nse_screener_router)


@api_router.get("/health")
def health_check():
    return {"status": "healthy", "service": "dad-of-anton-api"}
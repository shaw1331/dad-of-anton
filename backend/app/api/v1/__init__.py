from fastapi import APIRouter

from app.api.v1.workflow_routes import router as workflow_router

api_router = APIRouter()

api_router.include_router(workflow_router)


@api_router.get("/health")
def health_check():
    return {"status": "healthy", "service": "dad-of-anton-api"}
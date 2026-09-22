from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.routes.reports import router as reports_router
from app.core.config import get_cors_origins, get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, description="Read-only financial analytics for the Personal Finance platform")
app.add_middleware(CORSMiddleware, allow_origins=get_cors_origins(), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(OperationalError)
async def database_unavailable_handler(request, exc: OperationalError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "report-service"}


app.include_router(reports_router, prefix="/api/v1")

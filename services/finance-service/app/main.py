from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.routes.finance import router as finance_router
from app.core.config import get_cors_origins, get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(CORSMiddleware, allow_origins=get_cors_origins(), allow_origin_regex=r"https://[a-z0-9-]+\.vercel\.app", allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])


@app.exception_handler(OperationalError)
async def database_unavailable_handler(request, exc: OperationalError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "finance-service"}


app.include_router(finance_router, prefix="/api/v1")

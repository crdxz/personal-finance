from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.routes.auth import router as auth_router
from app.core.config import get_cors_origins, get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Authentication microservice for Personal Finance"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=r"https://[a-z0-9-]+\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(OperationalError)
async def database_unavailable_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable. Check DATABASE_URL and PostgreSQL connectivity."
        },
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok",
            "service": "auth-service"}


@app.get("/", include_in_schema=False)
def api_index() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


app.include_router(auth_router, prefix="/api/v1")

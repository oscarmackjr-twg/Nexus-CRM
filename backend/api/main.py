from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import asyncio as redis_async
from sqlalchemy import text
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from backend import __version__
from backend.api.middleware import (
    AuditLogMiddleware,
    OrgScopingMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from backend.api.routes import admin, ai_query, analytics, auth, automations, boards, companies, contacts, counterparties, deals, funding, funds, linkedin, orgs, pages, pipelines, tasks, teams, webhooks
from backend.config import settings
from backend.database import Base, get_engine, get_session_maker
from backend.utils.graceful_shutdown import install_signal_handlers
from backend.utils.structured_logging import setup_logging
from backend.utils.telemetry import setup_telemetry
from backend.workers.celery_app import celery_app

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
except ModuleNotFoundError:  # pragma: no cover
    Limiter = None
    _rate_limit_exceeded_handler = None
    RateLimitExceeded = None
    get_remote_address = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings)
    engine = get_engine()
    app.state.db_engine = engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.redis_client = redis_async.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    setup_telemetry(app, settings)
    try:
        install_signal_handlers(app, celery_app)
    except NotImplementedError:  # pragma: no cover
        pass
    yield
    await app.state.redis_client.aclose()
    await engine.dispose()


app = FastAPI(title="Nexus CRM", version=__version__, lifespan=lifespan)
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(OrgScopingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if Limiter is not None and get_remote_address is not None:
    limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
    app.state.limiter = limiter
    if RateLimitExceeded is not None and _rate_limit_exceeded_handler is not None:
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

for router in [
    admin.router,
    auth.router,
    orgs.router,
    teams.router,
    contacts.router,
    companies.router,
    pipelines.router,
    deals.router,
    counterparties.router,
    funds.router,
    funding.router,
    boards.router,
    tasks.router,
    pages.router,
    automations.router,
    ai_query.router,
    linkedin.router,
    webhooks.router,
    analytics.router,
]:
    app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "ok", "service": "nexus-crm"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__, "environment": settings.ENVIRONMENT}


async def check_database() -> None:
    session_factory = get_session_maker()
    async with session_factory() as session:
        await session.execute(text("SELECT 1"))


async def check_redis() -> None:
    client = redis_async.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        await client.ping()
    finally:
        await client.aclose()


async def check_storage() -> None:
    if settings.STORAGE_TYPE != "s3":
        return
    try:
        import boto3
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("boto3 is required for S3 readiness checks") from exc
    client = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
    client.head_bucket(Bucket=settings.S3_BUCKET_NAME)


async def _timed_check(name: str, fn) -> dict:
    started = perf_counter()
    try:
        await fn()
        return {"status": "ok", "latency_ms": round((perf_counter() - started) * 1000, 2)}
    except Exception as exc:
        return {"status": "error", "latency_ms": round((perf_counter() - started) * 1000, 2), "detail": str(exc)}


@app.get("/health/ready")
async def readiness_check():
    checks = {
        "database": await _timed_check("database", check_database),
        "redis": await _timed_check("redis", check_redis),
        "storage": await _timed_check("storage", check_storage),
    }
    has_errors = any(item["status"] != "ok" for item in checks.values())
    status_value = "ready" if not has_errors else "degraded"
    status_code = status.HTTP_200_OK if not has_errors else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        content={"status": status_value, "checks": checks},
        status_code=status_code,
    )


@app.get("/health/live")
async def liveness_check():
    return {"status": "alive"}


@app.get("/metrics")
async def prometheus_metrics(x_api_key: str | None = Header(default=None)):
    if settings.ENVIRONMENT == "production" and x_api_key != settings.METRICS_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    renderer = getattr(app.state, "metrics_renderer", None)
    content = renderer() if renderer is not None else ""
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config import get_settings
from app.db import build_engine, build_sessionmaker
from app.models import Base
from app.routers import demo_ap1, demo_ap2, demo_ap3, demo_ap4, demo_ap5, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = build_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.engine = engine
    app.state.sessionmaker = build_sessionmaker(engine)
    # Anti-pattern 2 (DI misuse) contrasts this lifespan-scoped singleton,
    # created once, against a "bad" dependency that builds a fresh client
    # per request.
    app.state.http_client = httpx.AsyncClient(timeout=10.0)

    yield

    await app.state.http_client.aclose()
    await engine.dispose()


app = FastAPI(title="Orders API — PyCon HK 2026 FastAPI performance demo", lifespan=lifespan)
app.include_router(orders.router)
app.include_router(demo_ap1.router)
app.include_router(demo_ap2.router)
app.include_router(demo_ap3.router)
app.include_router(demo_ap4.router)
app.include_router(demo_ap5.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

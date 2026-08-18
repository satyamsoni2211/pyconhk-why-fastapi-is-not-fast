import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/orders")
os.environ.setdefault("PAYMENT_GATEWAY_URL", "http://localhost:8080")

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class LifespanManager:
    """Minimal ASGI lifespan context manager (avoids adding asgi-lifespan as a dep)."""

    def __init__(self, app):
        self.app = app

    async def __aenter__(self):
        self._ctx = self.app.router.lifespan_context(self.app)
        await self._ctx.__aenter__()
        return self

    async def __aexit__(self, *exc_info):
        await self._ctx.__aexit__(*exc_info)

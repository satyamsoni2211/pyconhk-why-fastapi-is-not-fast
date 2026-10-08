import os

os.environ.setdefault("PAYMENT_GATEWAY_URL", "http://localhost:8080")

import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def payment_gateway():
    """Start the bundled mock gateway if nothing is listening on PAYMENT_GATEWAY_URL."""
    url = urlparse(os.environ["PAYMENT_GATEWAY_URL"])
    host, port = url.hostname, url.port or 80

    def listening() -> bool:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            return sock.connect_ex((host, port)) == 0

    if listening():
        yield
        return
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_gateway.main:app", "--port", str(port), "--log-level", "warning"]
    )
    try:
        for _ in range(50):
            if listening():
                break
            time.sleep(0.1)
        yield
    finally:
        proc.terminate()
        proc.wait()


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

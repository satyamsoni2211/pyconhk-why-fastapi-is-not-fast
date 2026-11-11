"""Shared setup for the demo scripts.

Makes every script runnable as `uv run scripts/<name>.py` from the
orders-api-demo folder, both on the host and inside the app container.
"""

import os
import socket
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Let scripts `import app...` without needing PYTHONPATH=.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Paths like benchmarks/... are relative to the project root.
os.chdir(PROJECT_ROOT)

# Docker Compose service names that only resolve inside the compose network.
_DOCKER_HOSTS = ("db", "payment-gateway", "app")


def _host_resolves(host: str) -> bool:
    try:
        socket.gethostbyname(host)
        return True
    except OSError:
        return False


def _localize(url: str) -> str:
    """Swap a compose service hostname for localhost when run from the host."""
    for host in _DOCKER_HOSTS:
        for sep in ("@", "//"):
            needle = f"{sep}{host}:"
            if needle in url and not _host_resolves(host):
                return url.replace(needle, f"{sep}localhost:")
    return url


def database_url() -> str:
    from app.config import get_settings

    return _localize(os.environ.get("DATABASE_URL") or get_settings().database_url)


def payment_gateway_url() -> str:
    from app.config import get_settings

    return _localize(
        os.environ.get("PAYMENT_GATEWAY_URL") or get_settings().payment_gateway_url
    )


def base_url() -> str:
    return os.environ.get("BASE_URL", "http://localhost:8000")

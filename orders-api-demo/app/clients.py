import httpx
from fastapi import Request


async def get_http_client(request: Request) -> httpx.AsyncClient:
    """The correct way: hand out the lifespan-scoped singleton (AP2 'good')."""
    return request.app.state.http_client

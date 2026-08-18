from contextlib import contextmanager

from sqlalchemy import event

from app.main import app


@contextmanager
def count_queries():
    counter = {"n": 0}

    def _count(*args, **kwargs):
        counter["n"] += 1

    sync_engine = app.state.engine.sync_engine
    event.listen(sync_engine, "before_cursor_execute", _count)
    try:
        yield counter
    finally:
        event.remove(sync_engine, "before_cursor_execute", _count)


async def test_bad_crash_raises_missing_greenlet(client):
    resp = await client.get("/demo/ap3/bad-crash?limit=3")
    assert resp.status_code == 500
    body = resp.json()
    assert "Greenlet" in body["error_type"]


async def test_bad_n1_issues_one_query_per_order(client):
    limit = 5
    with count_queries() as counter:
        resp = await client.get(f"/demo/ap3/bad-n1?limit={limit}")
    assert resp.status_code == 200
    # 1 query to list orders + 1 lazy-load query per order = limit + 1
    assert counter["n"] >= limit + 1, f"expected N+1 queries, got {counter['n']}"


async def test_good_uses_selectinload_with_few_queries(client):
    limit = 5
    with count_queries() as counter:
        resp = await client.get(f"/demo/ap3/good?limit={limit}")
    assert resp.status_code == 200
    # 1 query for orders + 1 batched selectinload query, regardless of limit
    assert counter["n"] <= 2, f"expected <=2 queries, got {counter['n']}"

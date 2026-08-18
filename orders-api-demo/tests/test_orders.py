import pytest


async def test_create_and_get_order(client):
    listed = await client.get("/orders?limit=1")
    assert listed.status_code == 200
    customer_id = listed.json()[0]["customer_id"]

    resp = await client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [{"sku": "TEST-1", "quantity": 2, "unit_price": 9.99}],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["customer_id"] == customer_id
    assert body["items"][0]["sku"] == "TEST-1"


async def test_list_orders(client):
    resp = await client.get("/orders?limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) <= 10


async def test_get_order_detail_for_seeded_order(client):
    listed = await client.get("/orders?limit=1")
    order_id = listed.json()[0]["id"]

    detail = await client.get(f"/orders/{order_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == order_id
    assert "items" in body


async def test_get_missing_order_404(client):
    resp = await client.get("/orders/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

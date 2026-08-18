async def test_bad_and_good_agree_on_item_counts(client):
    bad = await client.get("/demo/ap4/bad?limit=50")
    good = await client.get("/demo/ap4/good?limit=50")
    assert bad.status_code == 200
    assert good.status_code == 200
    assert bad.json()["n"] == good.json()["n"] == 50


async def test_bad_transform_is_slower_than_good(client):
    bad = await client.get("/demo/ap4/bad?limit=200")
    good = await client.get("/demo/ap4/good?limit=200")

    bad_elapsed = bad.json()["elapsed_seconds"]
    good_elapsed = good.json()["elapsed_seconds"]

    # Two redundant validation passes + per-field validators vs a single
    # from_attributes pass — a generous 1.3x threshold avoids flaking on
    # noisy CI while still catching a regression toward "no difference".
    assert bad_elapsed > good_elapsed * 1.3, (
        f"expected bad ({bad_elapsed * 1000:.2f}ms) to be meaningfully "
        f"slower than good ({good_elapsed * 1000:.2f}ms)"
    )

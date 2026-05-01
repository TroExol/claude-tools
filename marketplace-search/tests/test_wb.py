import json
from pathlib import Path
import pytest
from bin.marketplaces.wb import WildberriesAdapter, parse_search_response

FIXTURE = Path(__file__).parent / "fixtures" / "wb-search.json"


def test_parse_search_response_extracts_products():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    products = parse_search_response(raw)

    assert len(products) >= 5
    p = products[0]
    assert p.marketplace == "wb"
    assert p.title
    assert p.price > 0
    assert p.url.startswith("https://www.wildberries.ru/catalog/")
    assert p.url.endswith("/detail.aspx")
    assert p.in_stock is True


def test_parse_search_response_handles_old_price():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    products = parse_search_response(raw)
    has_discount = [p for p in products if p.old_price is not None]
    assert len(has_discount) > 0
    p = has_discount[0]
    assert p.old_price > p.price


def test_parse_search_response_handles_out_of_stock():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    products = parse_search_response(raw)
    out_of_stock = [p for p in products if not p.in_stock]
    assert len(out_of_stock) >= 1


@pytest.mark.asyncio
async def test_search_live_smoke():
    """Live smoke test - skipped in CI by default."""
    pytest.importorskip("curl_cffi")
    a = WildberriesAdapter()
    res = await a.search("телевизор samsung", max_per=10)
    assert isinstance(res.products, list)

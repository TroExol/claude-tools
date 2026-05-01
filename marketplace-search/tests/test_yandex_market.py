from pathlib import Path
import pytest
from bin.marketplaces.yandex_market import YandexMarketAdapter, parse_search_html

FIXTURE = Path(__file__).parent / "fixtures" / "yandex-search.html"


def test_parse_search_html_extracts_products():
    html = FIXTURE.read_text(encoding="utf-8")
    products = parse_search_html(html)

    assert len(products) >= 3, f"got {len(products)} products"
    p = products[0]
    assert p.marketplace == "yandex"
    assert p.title
    assert p.price > 0
    assert "market.yandex" in p.url
    assert p.marketplace_product_id.isdigit()


def test_parse_search_html_extracts_rating():
    html = FIXTURE.read_text(encoding="utf-8")
    products = parse_search_html(html)
    with_rating = [p for p in products if p.rating is not None]
    assert len(with_rating) > 0


@pytest.mark.asyncio
async def test_search_live_smoke():
    a = YandexMarketAdapter()
    res = await a.search("телевизор samsung", max_per=10)
    assert isinstance(res.products, list)

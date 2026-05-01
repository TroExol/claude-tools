from pathlib import Path
import pytest
from bin.marketplaces.citilink import CitilinkAdapter, parse_search_html

FIXTURE = Path(__file__).parent / "fixtures" / "citilink-search.html"


def test_parse_search_html_extracts_products():
    html = FIXTURE.read_text(encoding="utf-8")
    products = parse_search_html(html)
    assert len(products) >= 3, f"got {len(products)}"
    p = products[0]
    assert p.marketplace == "citilink"
    assert p.title
    assert p.price > 0
    assert p.url.startswith("https://www.citilink.ru/")


@pytest.mark.asyncio
async def test_search_live_smoke():
    a = CitilinkAdapter()
    res = await a.search("телевизор", max_per=10)
    assert isinstance(res.products, list)

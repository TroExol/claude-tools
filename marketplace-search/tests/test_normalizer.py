from bin.marketplaces.base import Product, AdapterResult
from bin.normalizer import dedupe_within_marketplace, aggregate


def _p(mp, pid, title, price):
    return Product(marketplace=mp, marketplace_product_id=str(pid),
                   title=title, price=price, url=f"https://x/{pid}",
                   in_stock=True, raw={})


def test_dedupe_within_marketplace_keeps_lowest_price():
    products = [
        _p("wb", "1", "Samsung TV 55", 5000000),
        _p("wb", "1", "Samsung TV 55", 4500000),
        _p("wb", "2", "Other TV", 3000000),
    ]
    deduped = dedupe_within_marketplace(products)
    assert len(deduped) == 2
    samsung = next(p for p in deduped if p.marketplace_product_id == "1")
    assert samsung.price == 4500000


def test_aggregate_keeps_cross_marketplace_dups():
    results = [
        AdapterResult("wb", [_p("wb", "1", "Samsung TV 55", 5000000)]),
        AdapterResult("ozon", [_p("ozon", "X", "Samsung TV 55", 4800000)]),
    ]
    products = aggregate(results)
    assert len(products) == 2
    marketplaces = {p.marketplace for p in products}
    assert marketplaces == {"wb", "ozon"}

from bin.marketplaces.base import Product, Review, AdapterResult


def test_product_minimal_construction():
    p = Product(
        marketplace="wb",
        marketplace_product_id="123",
        title="Test TV",
        price=4990000,  # копейки
        url="https://wb.ru/123",
        in_stock=True,
        raw={},
    )
    assert p.marketplace == "wb"
    assert p.price == 4990000
    assert p.old_price is None
    assert p.rating is None


def test_review_minimal_construction():
    r = Review(
        marketplace="wb",
        product_id="123",
        rating=5,
        text="Отлично",
    )
    assert r.rating == 5
    assert r.author is None


def test_adapter_result_aggregation():
    r1 = AdapterResult(marketplace="wb", products=[], errors=[])
    r2 = AdapterResult(marketplace="ozon", products=[], errors=["timeout"])
    assert r1.is_ok is True
    assert r2.is_ok is False

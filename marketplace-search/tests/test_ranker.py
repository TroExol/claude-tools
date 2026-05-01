from bin.marketplaces.base import Product
from bin.ranker import rank_search_mode, rank_discover_mode


def _p(mp, pid, price, rating, reviews):
    return Product(marketplace=mp, marketplace_product_id=str(pid),
                   title=f"P-{pid}", price=price, url="https://x",
                   in_stock=True, raw={}, rating=rating, reviews_count=reviews)


def test_rank_search_mode_prefers_high_rating_with_many_reviews():
    products = [
        _p("wb", "1", 5000000, 5.0, 5),
        _p("wb", "2", 5000000, 4.7, 2000),
        _p("wb", "3", 5000000, 3.2, 1000),
    ]
    ranked = rank_search_mode(products, budget=None)
    assert ranked[0].marketplace_product_id == "2"
    assert ranked[-1].marketplace_product_id == "3"


def test_rank_search_mode_respects_budget():
    products = [
        _p("wb", "1", 8000000, 4.8, 1000),
        _p("wb", "2", 5000000, 4.5, 1000),
    ]
    ranked = rank_search_mode(products, budget=6000000)
    assert ranked[0].marketplace_product_id == "2"


def test_rank_discover_mode_boosts_expert_endorsed():
    products = [
        _p("wb", "1", 5000000, 4.5, 1000),
        _p("wb", "2", 5000000, 4.5, 1000),
    ]
    expert_models = {"P-1": 0.9}
    ranked = rank_discover_mode(products, expert_models=expert_models, budget=None)
    assert ranked[0].marketplace_product_id == "1"

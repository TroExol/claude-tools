from __future__ import annotations
import math
from bin.marketplaces.base import Product


def _norm_rating(p: Product) -> float:
    return (p.rating or 0) / 5.0


def _norm_reviews(p: Product) -> float:
    n = p.reviews_count or 0
    return min(math.log10(n + 1) / 4.0, 1.0)


def _price_fit(p: Product, budget: int | None) -> float:
    if budget is None or budget == 0:
        return 0.5
    if p.price <= budget:
        return 1.0
    overshoot = (p.price - budget) / budget
    return max(0.0, 1.0 - overshoot)


def _delivery_score(p: Product) -> float:
    s = (p.delivery or "").lower()
    if "завтра" in s or "сегодня" in s:
        return 1.0
    if "2-3" in s or "1-2" in s:
        return 0.7
    if "5" in s:
        return 0.4
    return 0.5


def rank_search_mode(products: list[Product], budget: int | None) -> list[Product]:
    def score(p: Product) -> float:
        return (
            _norm_rating(p) * 0.40
            + _norm_reviews(p) * 0.20
            + _price_fit(p, budget) * 0.20
            + _delivery_score(p) * 0.10
            + (1.0 if p.in_stock else 0.0) * 0.10
        )
    return sorted(products, key=score, reverse=True)


def rank_discover_mode(
    products: list[Product],
    expert_models: dict[str, float],
    budget: int | None,
) -> list[Product]:
    def expert_signal(p: Product) -> float:
        title_lower = p.title.lower()
        best = 0.0
        for model_name, conf in expert_models.items():
            if model_name.lower() in title_lower:
                best = max(best, conf)
        return best

    def score(p: Product) -> float:
        return (
            expert_signal(p) * 0.25
            + _norm_rating(p) * 0.25
            + _norm_reviews(p) * 0.20
            + _price_fit(p, budget) * 0.20
            + _delivery_score(p) * 0.05
            + (1.0 if p.in_stock else 0.0) * 0.05
        )
    return sorted(products, key=score, reverse=True)

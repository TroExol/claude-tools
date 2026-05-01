from __future__ import annotations
from bin.marketplaces.base import Product, AdapterResult


def dedupe_within_marketplace(products: list[Product]) -> list[Product]:
    """Within single marketplace, dedup by product_id — keep lowest price."""
    by_id: dict[tuple[str, str], Product] = {}
    for p in products:
        key = (p.marketplace, p.marketplace_product_id)
        existing = by_id.get(key)
        if existing is None or p.price < existing.price:
            by_id[key] = p
    return list(by_id.values())


def aggregate(results: list[AdapterResult]) -> list[Product]:
    """Combine adapter results into single product list, dedupe per-marketplace.

    Cross-marketplace duplicates kept intentionally — useful for price comparison.
    """
    out: list[Product] = []
    for r in results:
        out.extend(dedupe_within_marketplace(r.products))
    return out

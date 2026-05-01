#!/usr/bin/env python
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bin.marketplaces.wb import WildberriesAdapter
from bin.marketplaces.yandex_market import YandexMarketAdapter
from bin.marketplaces.mvideo import MVideoAdapter
from bin.marketplaces.citilink import CitilinkAdapter
from bin.marketplaces.ozon import OzonAdapter
from bin.marketplaces.dns import DnsAdapter
from bin.normalizer import aggregate
from bin.orchestrator import search_all, top_popular_all


ADAPTERS = {
    "wb": WildberriesAdapter,
    "yandex": YandexMarketAdapter,
    "mvideo": MVideoAdapter,
    "citilink": CitilinkAdapter,
    "ozon": OzonAdapter,
    "dns": DnsAdapter,
}


def _resolve_adapters(spec: str) -> list:
    if spec == "all":
        names = list(ADAPTERS.keys())
    else:
        names = [n.strip() for n in spec.split(",") if n.strip()]
    return [ADAPTERS[n]() for n in names if n in ADAPTERS]


def _serialize_products(products) -> list[dict]:
    return [asdict(p) for p in products]


def _filter_strict(products, query: str):
    """Strict mode: keep only products where ALL query tokens (>=3 chars) appear in title."""
    import re as _re
    tokens = [t.lower() for t in _re.split(r"\s+", query.strip()) if len(t) >= 3]
    if not tokens:
        return products
    return [p for p in products if all(t in p.title.lower() for t in tokens)]


def _serialize_results(results, strict_query: str | None = None) -> dict:
    products = aggregate(results)
    if strict_query:
        products = _filter_strict(products, strict_query)
    return {
        "products": _serialize_products(products),
        "errors": [
            {"marketplace": r.marketplace, "errors": r.errors}
            for r in results if r.errors
        ],
        "stats": {
            r.marketplace: {"count": len(r.products), "ok": r.is_ok}
            for r in results
        },
    }


async def cmd_search(args) -> dict:
    adapters = _resolve_adapters(args.marketplaces)
    results = await search_all(adapters, args.query,
                               max_per=args.max_per, city=args.city,
                               timeout=args.timeout)
    return _serialize_results(results, strict_query=args.query if args.strict else None)


async def cmd_top_popular(args) -> dict:
    adapters = _resolve_adapters(args.marketplaces)
    results = await top_popular_all(adapters, args.category,
                                    limit=args.limit, city=args.city,
                                    timeout=args.timeout)
    return _serialize_results(results)


async def cmd_reviews(args) -> dict:
    cls = ADAPTERS[args.marketplace]
    a = cls()
    reviews = await a.reviews(args.product_id, limit=args.limit)
    return {"reviews": [asdict(r) for r in reviews]}


async def cmd_product(args) -> dict:
    cls = ADAPTERS[args.marketplace]
    a = cls()
    p = await a.product(args.product_id, city=args.city)
    return {"product": asdict(p) if p else None}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("--query", required=True)
    s.add_argument("--marketplaces", default="all", help="all or csv: wb,ozon,yandex,mvideo,citilink,dns")
    s.add_argument("--max-per", type=int, default=30)
    s.add_argument("--city", default="perm")
    s.add_argument("--timeout", type=int, default=60)
    s.add_argument("--strict", action="store_true",
                   help="Filter products to those with all query tokens in title (>=3 chars)")

    t = sub.add_parser("top-popular")
    t.add_argument("--category", required=True)
    t.add_argument("--marketplaces", default="all")
    t.add_argument("--limit", type=int, default=30)
    t.add_argument("--city", default="perm")
    t.add_argument("--timeout", type=int, default=60)

    r = sub.add_parser("reviews")
    r.add_argument("--marketplace", required=True, choices=list(ADAPTERS.keys()))
    r.add_argument("--product-id", required=True)
    r.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("product")
    p.add_argument("--marketplace", required=True, choices=list(ADAPTERS.keys()))
    p.add_argument("--product-id", required=True)
    p.add_argument("--city", default="perm")

    return parser


def main():
    # Force UTF-8 stdout/stderr — fixes UnicodeEncodeError на Windows cp1251
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    args = build_parser().parse_args()
    if args.cmd == "search":
        result = asyncio.run(cmd_search(args))
    elif args.cmd == "top-popular":
        result = asyncio.run(cmd_top_popular(args))
    elif args.cmd == "reviews":
        result = asyncio.run(cmd_reviews(args))
    elif args.cmd == "product":
        result = asyncio.run(cmd_product(args))
    else:
        sys.exit(f"unknown cmd: {args.cmd}")
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

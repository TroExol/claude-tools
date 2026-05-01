"""
Wildberries adapter — v18 search endpoint.

Endpoint: https://search.wb.ru/exactmatch/ru/common/v18/search?...
Response shape (key fields):
  {
    "products": [
      {
        "id": 123,
        "name": "...",
        "brand": "...",
        "rating": 4.8,
        "feedbacks": 1234,
        "totalQuantity": 5,
        "sizes": [{"price": {"basic": 599000, "product": 499000, ...}}]
      }
    ]
  }
Цена в копейках. `sizes[0].price.product` — текущая цена, `basic` — старая (если выше).
URL карточки: https://www.wildberries.ru/catalog/{id}/detail.aspx
"""
from __future__ import annotations
from urllib.parse import quote
from typing import Any

from bin.http_client import make_session
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product, Review

WB_DEST = "-1257786"
WB_SEARCH_URL = (
    "https://search.wb.ru/exactmatch/ru/common/v18/search"
    "?appType=1&curr=rub&dest={dest}&lang=ru&page=1&query={query}"
    "&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
)
WB_FEEDBACKS_URL = "https://feedbacks{shard}.wb.ru/feedbacks/v2/{nm_id}"


def _wb_url(nm_id: int | str) -> str:
    return f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"


def _wb_image_url(nm_id: int) -> str:
    short = nm_id // 100000
    if short <= 143: basket = "01"
    elif short <= 287: basket = "02"
    elif short <= 431: basket = "03"
    elif short <= 719: basket = "04"
    elif short <= 1007: basket = "05"
    elif short <= 1061: basket = "06"
    elif short <= 1115: basket = "07"
    elif short <= 1169: basket = "08"
    elif short <= 1313: basket = "09"
    elif short <= 1601: basket = "10"
    elif short <= 1655: basket = "11"
    elif short <= 1919: basket = "12"
    elif short <= 2045: basket = "13"
    elif short <= 2189: basket = "14"
    elif short <= 2405: basket = "15"
    elif short <= 2621: basket = "16"
    elif short <= 2837: basket = "17"
    elif short <= 3053: basket = "18"
    elif short <= 3269: basket = "19"
    elif short <= 3485: basket = "20"
    elif short <= 3701: basket = "21"
    elif short <= 3917: basket = "22"
    elif short <= 4133: basket = "23"
    elif short <= 4349: basket = "24"
    elif short <= 4565: basket = "25"
    else: basket = "26"
    vol = nm_id // 100000
    part = nm_id // 1000
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/c246x328/1.webp"


def _extract_price(raw: dict[str, Any]) -> tuple[int, int | None]:
    """Return (price, old_price) in копейках. v18 stores price in sizes[0].price."""
    sizes = raw.get("sizes") or []
    if sizes and isinstance(sizes[0], dict):
        price_obj = sizes[0].get("price") or {}
        product_price = price_obj.get("product") or 0
        basic = price_obj.get("basic") or 0
        # WB price already in копейки * 100? Habr article divides by 100 to get rubles,
        # so price.product is in копейках (e.g. 33700 = 337 руб) — but historical WB used /100.
        # v18 example: "basic":160000,"product":33700 → 1600 руб vs 337 руб → /100 means копейки.
        if product_price:
            old = basic if basic and basic > product_price else None
            return product_price, old
    # fallback to legacy fields if any
    sale = raw.get("salePriceU") or raw.get("priceU") or 0
    old_u = raw.get("priceU")
    old = old_u if old_u and old_u > sale else None
    return sale, old


def parse_search_response(data: dict[str, Any]) -> list[Product]:
    """Extract products from v18 WB response.

    v18 returns products at top level (`data.products`), not under `data.data.products`.
    Older v13 wraps in `data.data.products`; we support both.
    """
    raw_products = data.get("products") or data.get("data", {}).get("products") or []
    products: list[Product] = []
    for raw in raw_products:
        nm_id = raw.get("id")
        if not nm_id:
            continue
        price, old_price = _extract_price(raw)
        products.append(
            Product(
                marketplace="wb",
                marketplace_product_id=str(nm_id),
                title=(raw.get("name") or "").strip() or "—",
                price=price,
                old_price=old_price,
                rating=raw.get("reviewRating") or raw.get("rating") or None,
                reviews_count=raw.get("nmFeedbacks") or raw.get("feedbacks") or None,
                url=_wb_url(nm_id),
                image_url=_wb_image_url(nm_id),
                delivery=None,
                in_stock=raw.get("totalQuantity", 0) > 0,
                raw=raw,
            )
        )
    return products


class WildberriesAdapter(BaseAdapter):
    name = "wb"

    async def search(self, query: str, max_per: int = 30, city: str = "perm") -> AdapterResult:
        url = WB_SEARCH_URL.format(dest=WB_DEST, query=quote(query))
        try:
            with make_session() as s:
                r = s.get(url, timeout=30)
                if r.status_code != 200:
                    return AdapterResult(self.name, [], [f"HTTP {r.status_code}"])
                data = r.json()
        except Exception as e:
            return AdapterResult(self.name, [], [f"WB search error: {e}"])
        products = parse_search_response(data)[:max_per]
        return AdapterResult(self.name, products)

    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        res = await self.search(product_id, max_per=5)
        for p in res.products:
            if p.marketplace_product_id == str(product_id):
                return p
        return None

    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        try:
            nm_id = int(product_id)
        except ValueError:
            return []
        shard = "1" if nm_id % 1000000 <= 439660 else "2"
        url = WB_FEEDBACKS_URL.format(shard=shard, nm_id=nm_id)
        try:
            with make_session() as s:
                r = s.get(url, timeout=30)
                if r.status_code != 200:
                    return []
                data = r.json()
        except Exception:
            return []

        out: list[Review] = []
        for raw in (data.get("feedbacks") or [])[:limit]:
            out.append(
                Review(
                    marketplace="wb",
                    product_id=product_id,
                    rating=raw.get("productValuation") or 0,
                    text=raw.get("text") or "",
                    author=(raw.get("wbUserDetails") or {}).get("name"),
                    date=raw.get("createdDate"),
                    pros=raw.get("pros"),
                    cons=raw.get("cons"),
                    helpful_count=None,
                )
            )
        return out

    async def top_popular(self, category: str, limit: int = 30, city: str = "perm") -> AdapterResult:
        return await self.search(category, max_per=limit, city=city)

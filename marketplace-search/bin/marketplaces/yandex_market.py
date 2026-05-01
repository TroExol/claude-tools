"""
Я.Маркет adapter — DOM parsing of productSnippet zones.

Я.Маркет рендерит результаты поиска в SSR HTML с зонами `data-zone-name="productSnippet"`.
Внутри каждой зоны:
  - `data-zone-name="title"` или `data-auto="snippet-title"` — title
  - `data-auto="snippet-price-current"` — текущая цена
  - `data-auto="reviews"` или `data-zone-name="rating"` — рейтинг + кол-во отзывов
  - `<a href="/card/{slug}/{id}">` — URL карточки

При SmartCaptcha (HTTP 429 / showcaptcha redirect) — возвращаем ошибку.
"""
from __future__ import annotations
import re
from urllib.parse import quote
from typing import Any

from selectolax.parser import HTMLParser

from bin.http_client import make_session
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product, Review


YM_SEARCH_URL = "https://market.yandex.ru/search?text={query}"
YM_DOMAIN = "https://market.yandex.ru"


def _parse_price(text: str) -> int:
    """Extract price from text like '49 422 ₽' → 4942200 (копейки)."""
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) * 100 if digits else 0


def _parse_rating_block(text: str) -> tuple[float | None, int | None]:
    """Extract rating + reviews count from text like '4.8(282) · 1K купили'."""
    rating = None
    reviews = None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*\(", text)
    if m:
        try:
            rating = float(m.group(1).replace(",", "."))
        except ValueError:
            pass
    m = re.search(r"\((\d+)\)", text)
    if m:
        reviews = int(m.group(1))
    return rating, reviews


def _extract_product_id(href: str) -> str | None:
    """From /card/{slug}/{id}?... extract id."""
    m = re.search(r"/card/[^/?]+/(\d+)", href)
    return m.group(1) if m else None


def parse_search_html(html: str) -> list[Product]:
    tree = HTMLParser(html)
    products: list[Product] = []
    seen: set[str] = set()

    for card in tree.css('[data-zone-name="productSnippet"]'):
        title_node = card.css_first('[data-auto="snippet-title"]') or card.css_first('[data-zone-name="title"]')
        price_node = card.css_first('[data-auto="snippet-price-current"]')
        link_node = card.css_first('a[href*="/card/"]')
        if not (title_node and price_node and link_node):
            continue

        title = title_node.text(strip=True)
        price = _parse_price(price_node.text())
        if not title or not price:
            continue

        href = link_node.attributes.get("href", "")
        pid = _extract_product_id(href)
        if not pid or pid in seen:
            continue
        seen.add(pid)

        # Rating block
        rating_node = card.css_first('[data-auto="reviews"]') or card.css_first('[data-zone-name="rating"]')
        rating = None
        reviews_count = None
        if rating_node:
            rating, reviews_count = _parse_rating_block(rating_node.text(strip=True))

        # URL: relative → absolute
        url = href if href.startswith("http") else YM_DOMAIN + href

        products.append(
            Product(
                marketplace="yandex",
                marketplace_product_id=pid,
                title=title,
                price=price,
                rating=rating,
                reviews_count=reviews_count,
                url=url,
                in_stock=True,
                raw={"source": "dom"},
            )
        )
    return products


class YandexMarketAdapter(BaseAdapter):
    name = "yandex"

    async def search(self, query: str, max_per: int = 30, city: str = "perm") -> AdapterResult:
        url = YM_SEARCH_URL.format(query=quote(query))
        try:
            with make_session() as s:
                r = s.get(url, timeout=30)
                if r.status_code in (429, 403) or "showcaptcha" in str(r.url):
                    return AdapterResult(self.name, [], ["captcha"])
                if r.status_code != 200:
                    return AdapterResult(self.name, [], [f"HTTP {r.status_code}"])
                products = parse_search_html(r.text)[:max_per]
                return AdapterResult(self.name, products)
        except Exception as e:
            return AdapterResult(self.name, [], [f"yandex search error: {e}"])

    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        url = f"{YM_DOMAIN}/product/{product_id}"
        try:
            with make_session() as s:
                r = s.get(url, timeout=30)
                if r.status_code != 200:
                    return None
                products = parse_search_html(r.text)
                return products[0] if products else None
        except Exception:
            return None

    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        return []  # Я.Маркет review API требует auth — отложено

    async def top_popular(self, category: str, limit: int = 30, city: str = "perm") -> AdapterResult:
        return await self.search(category, max_per=limit, city=city)

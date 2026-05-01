"""
Ситилинк adapter — DOM parsing of SnippetProductVerticalLayout cards.

Карточки рендерятся клиентом, поэтому статическая HTTP-фикстура — skeleton.
Live: helper.py search использует HTTP fallback (curl_cffi). Если карточки
не заполнены, возвращаем 0 продуктов (фронт явно блокирует ботов).
Capture фикстур делается через Playwright (см. tests/capture_fixtures.py).

Selectors (после client hydration):
  - `[data-meta-name="SnippetProductVerticalLayout"]` — карточка
  - `data-meta-product-id` — product id
  - `a[href][title]` внутри карточки — title attr
  - `[data-meta-name="Snippet__price"]` — current price
  - `[data-meta-name="MetaInfo_rating"]` — rating
  - `[data-meta-name="MetaInfo_opinionsCount"]` — reviews count
"""
from __future__ import annotations
import re
from urllib.parse import quote

from selectolax.parser import HTMLParser

from bin.browser import fetch_html
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product, Review


CL_SEARCH_URL = "https://www.citilink.ru/search/?text={query}"
CL_DOMAIN = "https://www.citilink.ru"


def _parse_price(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) * 100 if digits else 0


def _parse_rating(text: str) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)", text or "")
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except ValueError:
            pass
    return None


def _parse_count(text: str) -> int | None:
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) if digits else None


def parse_search_html(html: str) -> list[Product]:
    tree = HTMLParser(html)
    products: list[Product] = []
    seen: set[str] = set()

    for card in tree.css('[data-meta-name="SnippetProductVerticalLayout"]'):
        pid = card.attributes.get("data-meta-product-id") or ""
        if not pid or pid in seen:
            continue

        link = card.css_first('a[href][title]')
        if not link:
            continue
        title = link.attributes.get("title", "").strip()
        href = link.attributes.get("href", "")
        if not title or not href:
            continue

        price_node = card.css_first('[data-meta-name="Snippet__price"]')
        price = _parse_price(price_node.text()) if price_node else 0
        if not price:
            continue

        rating_node = card.css_first('[data-meta-name="MetaInfo_rating"]')
        rating = _parse_rating(rating_node.text()) if rating_node else None
        reviews_node = card.css_first('[data-meta-name="MetaInfo_opinionsCount"]')
        reviews = _parse_count(reviews_node.text()) if reviews_node else None

        url = href if href.startswith("http") else CL_DOMAIN + href
        seen.add(pid)
        products.append(
            Product(
                marketplace="citilink",
                marketplace_product_id=pid,
                title=title,
                price=price,
                rating=rating,
                reviews_count=reviews,
                url=url,
                in_stock=True,
                raw={"source": "dom"},
            )
        )
    return products


class CitilinkAdapter(BaseAdapter):
    name = "citilink"

    async def search(self, query: str, max_per: int = 30, city: str = "perm") -> AdapterResult:
        url = CL_SEARCH_URL.format(query=quote(query))
        try:
            html = await fetch_html(
                url,
                wait_function="""() => {
                    const el = document.querySelector('[data-meta-name="SnippetProductVerticalLayout"]');
                    return el && el.getAttribute('data-meta-product-id');
                }""",
                wait_timeout_ms=25000,
            )
            products = parse_search_html(html)[:max_per]
            if not products:
                return AdapterResult(self.name, [], ["citilink: 0 products"])
            return AdapterResult(self.name, products)
        except Exception as e:
            return AdapterResult(self.name, [], [f"citilink error: {e}"])

    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        return None

    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        return []

    async def top_popular(self, category: str, limit: int = 30, city: str = "perm") -> AdapterResult:
        return await self.search(category, max_per=limit, city=city)

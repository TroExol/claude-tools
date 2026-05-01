"""
DNS adapter — Playwright DOM parsing + opinion CDP scraper.

DNS блокируется Qrator (HTTP 403 при curl_cffi). Через Playwright + достаточное
ожидание JS-challenge обычно проходит. Reviews → CDP с pagination "Показать ещё".

Card structure:
  - `a[href*="/product/"]` — product link
  - title в `<a>` text или nearby `[class*="title"]`
  - цена в parent `[class*="price"]`

Opinion card structure:
  - `.ow-opinion[data-opinion-id]` — карточка
  - `.profile-info__name` — автор
  - `.ow-opinion__date` — дата
  - `.star-rating__star[data-state="selected"]` — заполненные звёзды (count = rating)
  - `.ow-opinion__info-list-item` → `.ow-opinion__info-title` + `.ow-opinion__info-desc`
"""
from __future__ import annotations
import re
from urllib.parse import quote

from selectolax.parser import HTMLParser

from bin.browser import fetch_html
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product, Review


DNS_SEARCH_URL = "https://www.dns-shop.ru/search/?q={query}"
DNS_DOMAIN = "https://www.dns-shop.ru"
PRICE_RE = re.compile(r"(\d[\d\s  ]{2,})\s*₽")
ID_RE = re.compile(r"/product/([a-f0-9]{8,})/?")


def _parse_price(text: str) -> int:
    m = PRICE_RE.search(text or "")
    if not m:
        return 0
    digits = re.sub(r"[^\d]", "", m.group(1))
    return int(digits) * 100 if digits else 0


async def _fetch_dns_reviews(product_id: str, limit: int) -> str:
    """Open DNS opinion page via CDP. Two-step: product page → resolve slug → opinion URL.

    DNS opinion final URL format: /product/opinion/{id}/{slug}/
    Прямой запрос /product/{id}/opinion/ редиректит на product page без отзывов.
    """
    import os
    from playwright.async_api import async_playwright
    cdp = os.environ.get("MARKETPLACE_CDP_URL", "http://127.0.0.1:9222")
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()
        try:
            # Step 1: get slug via product page redirect
            await page.goto(f"{DNS_DOMAIN}/product/{product_id}/", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            final_url = page.url  # /product/{id}/{slug}/
            # Step 2: append /opinion/ to slug-resolved URL
            opinion_url = final_url.rstrip("/") + "/opinion/"
            await page.goto(opinion_url, wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_selector('.ow-opinion[data-opinion-id]', timeout=20000)
            except Exception:
                pass
            await page.wait_for_timeout(2000)
            # Pagination: "Показать ещё" button
            for _ in range(15):
                count = await page.locator('.ow-opinion[data-opinion-id]').count()
                if count >= limit:
                    break
                btn = page.locator('.paginator-widget__more').first
                try:
                    if await btn.is_visible(timeout=2000):
                        await btn.scroll_into_view_if_needed()
                        await btn.click(timeout=3000)
                        await page.wait_for_timeout(2000)
                    else:
                        break
                except Exception:
                    break
            return await page.content()
        finally:
            await page.close()


def _parse_dns_reviews(html: str, product_id: str, limit: int) -> list[Review]:
    tree = HTMLParser(html)
    out: list[Review] = []
    for card in tree.css('.ow-opinion[data-opinion-id]')[:limit]:
        author_node = card.css_first('.profile-info__name')
        author = author_node.text(strip=True) if author_node else None
        date_node = card.css_first('.ow-opinion__date')
        date = date_node.text(strip=True) if date_node else None
        # DNS дублирует звёзды (desktop+mobile вариант) → делим на 2
        sel_count = len(card.css('.star-rating__star[data-state="selected"]'))
        total_stars = len(card.css('.star-rating__star'))
        rating = sel_count // 2 if total_stars >= 10 else sel_count
        # Pros/Cons/Comment в .ow-opinion__texts → .ow-opinion__text
        pros = None
        cons = None
        body_parts: list[str] = []
        for block in card.css('.ow-opinion__text'):
            title_node = block.css_first('.ow-opinion__text-title')
            desc_node = block.css_first('.ow-opinion__text-desc')
            if not title_node or not desc_node:
                continue
            title_text = title_node.text(strip=True).lower()
            desc_text = desc_node.text(separator=' ', strip=True)
            if 'достоин' in title_text:
                pros = desc_text
            elif 'недостат' in title_text:
                cons = desc_text
            else:
                body_parts.append(desc_text)
        body = "\n".join(body_parts) if body_parts else ""
        out.append(Review(
            marketplace="dns",
            product_id=product_id,
            rating=rating,
            text=body,
            author=author,
            date=date,
            pros=pros,
            cons=cons,
            helpful_count=None,
        ))
    return out


def parse_search_html(html: str) -> list[Product]:
    if "HTTP 403" in html or "qrator" in html.lower()[:5000]:
        return []
    tree = HTMLParser(html)
    products: list[Product] = []
    seen: set[str] = set()

    for link in tree.css('a[href*="/product/"]'):
        href = link.attributes.get("href", "")
        m = ID_RE.search(href)
        if not m:
            continue
        pid = m.group(1)
        if pid in seen:
            continue

        title = link.text(strip=True) or (link.attributes.get("title") or "")
        if not title or len(title) < 5:
            continue

        price = 0
        parent = link.parent
        for _ in range(6):
            if parent is None:
                break
            price = _parse_price(parent.text())
            if price:
                break
            parent = parent.parent
        if not price:
            continue

        url = href if href.startswith("http") else DNS_DOMAIN + href
        seen.add(pid)
        products.append(
            Product(
                marketplace="dns",
                marketplace_product_id=pid,
                title=title[:200],
                price=price,
                url=url,
                in_stock=True,
                raw={"source": "dom"},
            )
        )
    return products


class DnsAdapter(BaseAdapter):
    name = "dns"

    async def search(self, query: str, max_per: int = 30, city: str = "perm") -> AdapterResult:
        url = DNS_SEARCH_URL.format(query=quote(query))
        try:
            html = await fetch_html(
                url,
                wait_selector='a[href*="/product/"]',
                wait_timeout_ms=30000,
                extra_wait_ms=3000,
                use_profile="dns",
            )
            products = parse_search_html(html)[:max_per]
            if not products:
                return AdapterResult(self.name, [], ["dns: Qrator challenge or 0 products"])
            return AdapterResult(self.name, products)
        except Exception as e:
            return AdapterResult(self.name, [], [f"dns error: {e}"])

    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        return None

    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        try:
            html = await _fetch_dns_reviews(product_id, limit)
        except Exception:
            return []
        return _parse_dns_reviews(html, product_id, limit)

    async def top_popular(self, category: str, limit: int = 30, city: str = "perm") -> AdapterResult:
        return await self.search(category, max_per=limit, city=city)

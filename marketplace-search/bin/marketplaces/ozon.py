"""
Ozon adapter — Playwright DOM parsing.

Ozon SSR блокируется antibot-страницей "Доступ ограничен". Через
Playwright + достаточное ожидание JS-challenge может пройти.
Cookie persistence (browser.warmup_and_save_cookies) для будущих запросов.

Card structure:
  - `[data-widget="searchResultsV2"]` контейнер
  - `div[data-index]` карточки
  - `a[href*="/product/"]` — title + URL
  - `span` с ценой через regex
"""
from __future__ import annotations
import re
from urllib.parse import quote

from selectolax.parser import HTMLParser

from bin.browser import fetch_html
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product, Review


async def _fetch_ozon_reviews(url: str, limit: int) -> tuple[str, dict]:
    """Open Ozon reviews page via CDP, scroll to load `limit` reviews,
    return (html, {uuid: rating} dict)."""
    import os
    from playwright.async_api import async_playwright
    cdp = os.environ.get("MARKETPLACE_CDP_URL", "http://127.0.0.1:9222")
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_selector('[data-review-uuid]', timeout=20000)
            except Exception:
                pass
            await page.wait_for_timeout(2000)
            # Scroll to load more reviews
            for _ in range(20):
                count = await page.locator('[data-review-uuid]').count()
                if count >= limit:
                    break
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
            # Extract ratings via JS — first 5 svg colors per card
            ratings = await page.evaluate("""
                () => {
                    const out = {};
                    document.querySelectorAll('[data-review-uuid]').forEach(card => {
                        const svgs = card.querySelectorAll('svg');
                        let r = 0;
                        for (let i = 0; i < Math.min(5, svgs.length); i++) {
                            const path = svgs[i].querySelector('path');
                            if (!path) continue;
                            const fill = getComputedStyle(path).fill || '';
                            // orange/yellow filled star
                            if (/255,\\s*1[5-9]\\d|255,\\s*2\\d\\d/.test(fill) || fill.includes('255, 165')) {
                                r++;
                            }
                        }
                        out[card.getAttribute('data-review-uuid')] = r;
                    });
                    return out;
                }
            """)
            html = await page.content()
            return html, ratings
        finally:
            await page.close()


def _parse_ozon_reviews(html: str, product_id: str, ratings: dict, limit: int) -> list[Review]:
    import re as _re
    tree = HTMLParser(html)
    out: list[Review] = []
    for card in tree.css('[data-review-uuid]')[:limit]:
        uuid = card.attributes.get('data-review-uuid', '')
        text_pipe = card.text(separator='|', strip=True)
        parts = [p for p in text_pipe.split('|') if p]
        # Date pattern (skip when looking for author)
        date_re = _re.compile(r'^\d{1,2}\s+\w+\s+\d{4}$|^изменен')
        # Author — first short non-date token (1-30 chars, no digits)
        author = None
        for p in parts[:5]:
            if len(p) >= 2 and len(p) <= 40 and not date_re.search(p) and not _re.search(r'^\d', p):
                author = p
                break
        # Date
        date_m = _re.search(r'(?:изменен\s+)?(\d{1,2}\s+\w+\s+\d{4})', text_pipe)
        date = date_m.group(1) if date_m else None
        # Helpful count
        help_m = _re.search(r'Да\s+(\d+)', text_pipe)
        helpful = int(help_m.group(1)) if help_m else None
        # Review body — heuristic: longest natural text segment
        body_candidates = [p for p in parts if len(p) > 30 and not _re.search(r'^Да\s+\d+$|^Нет\s+\d+$|^Ответить$|комментар|помог этот', p)]
        body = max(body_candidates, key=len) if body_candidates else ""
        out.append(Review(
            marketplace="ozon",
            product_id=product_id,
            rating=ratings.get(uuid, 0),
            text=body,
            author=author,
            date=date,
            pros=None,
            cons=None,
            helpful_count=helpful,
        ))
    return out


OZON_SEARCH_URL = "https://www.ozon.ru/search/?text={query}"
OZON_DOMAIN = "https://www.ozon.ru"
PRICE_RE = re.compile(r"(\d[\d   ]{2,})\s*₽")
ID_RE = re.compile(r"/product/[^/]*-(\d{6,})/?")


def _parse_price(text: str) -> int:
    m = PRICE_RE.search(text or "")
    if not m:
        return 0
    digits = re.sub(r"[^\d]", "", m.group(1))
    return int(digits) * 100 if digits else 0


def parse_search_html(html: str) -> list[Product]:
    if "Доступ ограничен" in html or "Antibot" in html:
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

        title = (link.attributes.get("title") or link.text(strip=True))[:200]
        if not title or len(title) < 5:
            continue

        # Find price in ancestors
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

        url = href if href.startswith("http") else OZON_DOMAIN + href
        seen.add(pid)
        products.append(
            Product(
                marketplace="ozon",
                marketplace_product_id=pid,
                title=title,
                price=price,
                url=url,
                in_stock=True,
                raw={"source": "dom"},
            )
        )
    return products


class OzonAdapter(BaseAdapter):
    name = "ozon"

    async def search(self, query: str, max_per: int = 30, city: str = "perm") -> AdapterResult:
        url = OZON_SEARCH_URL.format(query=quote(query))
        try:
            html = await fetch_html(
                url,
                wait_selector='a[href*="/product/"]',
                wait_timeout_ms=30000,
                extra_wait_ms=3000,
                use_profile="ozon",
            )
            products = parse_search_html(html)[:max_per]
            if not products:
                return AdapterResult(self.name, [], ["ozon: antibot challenge or 0 products"])
            return AdapterResult(self.name, products)
        except Exception as e:
            return AdapterResult(self.name, [], [f"ozon error: {e}"])

    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        return None

    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        url = f"{OZON_DOMAIN}/product/{product_id}/reviews/"
        try:
            html, ratings = await _fetch_ozon_reviews(url, limit)
        except Exception as e:
            return [Review(marketplace="ozon", product_id=product_id, rating=0,
                           text=f"ozon reviews error: {e}", author=None, date=None,
                           pros=None, cons=None, helpful_count=None)][:0]
        return _parse_ozon_reviews(html, product_id, ratings, limit)

    async def top_popular(self, category: str, limit: int = 30, city: str = "perm") -> AdapterResult:
        return await self.search(category, max_per=limit, city=city)

r"""
МВидео adapter — DOM parsing of /products/* links.

Card structure (post-hydration):
  - `<a href="/products/{slug}-{id}">` — product link, id в конце после "-"
  - text content link mixes badges/bonus/price/buttons
  - "+5 90354 990 ₽" — это бонус 5903 + цена 54990. Берём МАКСИМУМ.
"""
from __future__ import annotations
import re
from urllib.parse import quote

from selectolax.parser import HTMLParser

from bin.browser import fetch_html
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product, Review


MV_SEARCH_URL = "https://www.mvideo.ru/search?q={query}"
MV_DOMAIN = "https://www.mvideo.ru"
PRICE_RE = re.compile(r"(\d[\d\s  ]{3,})\s*₽")
ID_RE = re.compile(r"-(\d{6,})/?$")


def _extract_price(text: str) -> int:
    """Берём максимальную из всех цен в text — реальная цена. Бонусы <5000.
    Возвращает копейки."""
    if not text:
        return 0
    matches = PRICE_RE.findall(text)
    prices = []
    for m in matches:
        digits = re.sub(r"[^\d]", "", m)
        if digits:
            prices.append(int(digits))
    return max(prices) * 100 if prices else 0


def _extract_bonus(text: str) -> int:
    """Минимум из цен — обычно бонус (если несколько цифр с ₽)."""
    if not text:
        return 0
    matches = PRICE_RE.findall(text)
    if len(matches) < 2:
        return 0
    prices = []
    for m in matches:
        digits = re.sub(r"[^\d]", "", m)
        if digits:
            prices.append(int(digits))
    return min(prices) if len(prices) >= 2 else 0


async def _fetch_mvideo_reviews(product_id: str, limit: int) -> str:
    """Open MVideo product page via CDP, scroll to reviews carousel, return html.

    MVideo /otzyvy redirects to product page. Reviews live in carousel
    `[itemprop="review"]` (5 popular reviews on product page).
    """
    import os
    from playwright.async_api import async_playwright
    cdp = os.environ.get("MARKETPLACE_CDP_URL", "http://127.0.0.1:9222")
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()
        try:
            await page.goto(f"{MV_DOMAIN}/products/{product_id}",
                            wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            # Scroll page to trigger lazy review carousel render
            for _ in range(8):
                await page.evaluate("window.scrollBy(0, 1000)")
                await page.wait_for_timeout(1000)
            try:
                await page.wait_for_selector('[itemprop="review"]', timeout=5000)
            except Exception:
                pass
            return await page.content()
        finally:
            await page.close()


def _parse_mvideo_reviews(html: str, product_id: str, limit: int) -> list[Review]:
    tree = HTMLParser(html)
    out: list[Review] = []
    for card in tree.css('[itemprop="review"]')[:limit]:
        # Author: [itemprop="author"] [itemprop="name"]
        author_node = card.css_first('[itemprop="author"] [itemprop="name"]')
        author = author_node.text(strip=True) if author_node else None
        # Date: [itemprop="datePublished"][content]
        date_node = card.css_first('[itemprop="datePublished"]')
        date = None
        if date_node:
            date = date_node.attributes.get('content') or date_node.text(strip=True)
        # Rating: [itemprop="ratingValue"][content]
        rating = 0
        rv_node = card.css_first('[itemprop="ratingValue"]')
        if rv_node:
            content = rv_node.attributes.get('content', '0')
            try:
                rating = int(float(content))
            except ValueError:
                pass
        # Body, pros, cons via .content__title + .content__text pairs
        pros = None
        cons = None
        body_parts: list[str] = []
        # Walk content children sequentially: title → text
        content_node = card.css_first('.content')
        if content_node:
            children = list(content_node.iter())
            i = 0
            while i < len(children):
                el = children[i]
                cls = el.attributes.get('class', '') if hasattr(el, 'attributes') else ''
                if 'content__title' in cls:
                    title_text = el.text(strip=True).lower()
                    # find next content__text
                    if i + 1 < len(children):
                        nxt = children[i + 1]
                        nxt_cls = nxt.attributes.get('class', '') if hasattr(nxt, 'attributes') else ''
                        if 'content__text' in nxt_cls:
                            desc_text = nxt.text(separator=' ', strip=True)
                            if 'плюс' in title_text or 'достоин' in title_text:
                                pros = desc_text
                            elif 'минус' in title_text or 'недостат' in title_text:
                                cons = desc_text
                            else:
                                body_parts.append(desc_text)
                            i += 2
                            continue
                i += 1
        # Fallback: itemprop=reviewBody
        if not body_parts:
            body_node = card.css_first('[itemprop="reviewBody"]')
            if body_node:
                body_parts.append(body_node.text(separator=' ', strip=True))
        body = "\n".join(body_parts) if body_parts else ""
        out.append(Review(
            marketplace="mvideo",
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


def _extract_title(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\d[\d\s  ]*\s*₽", " ", text)
    cleaned = re.sub(r"[Вв]\s*корзину|[Дд]обавить в избранное|НДС в твою пользу", " ", cleaned)
    cleaned = re.sub(r"\(\d+\)|\d+\.\d+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:200]


def parse_search_html(html: str) -> list[Product]:
    tree = HTMLParser(html)
    products: list[Product] = []
    seen: set[str] = set()

    for link in tree.css('a[href*="/products/"]'):
        href = link.attributes.get("href", "")
        m = ID_RE.search(href)
        if not m:
            continue
        pid = m.group(1)
        if pid in seen:
            continue

        text = link.text(strip=True)
        price = _extract_price(text)
        bonus = _extract_bonus(text)
        if not price:
            parent = link.parent
            for _ in range(5):
                if parent is None:
                    break
                price = _extract_price(parent.text())
                if price:
                    bonus = _extract_bonus(parent.text())
                    break
                parent = parent.parent
        if not price:
            continue

        title = _extract_title(text)
        if not title or len(title) < 5:
            continue

        url = href if href.startswith("http") else MV_DOMAIN + href
        seen.add(pid)
        products.append(
            Product(
                marketplace="mvideo",
                marketplace_product_id=pid,
                title=title,
                price=price,
                url=url,
                in_stock=True,
                raw={"source": "dom", "bonus": bonus},
            )
        )
    return products


class MVideoAdapter(BaseAdapter):
    name = "mvideo"

    async def search(self, query: str, max_per: int = 30, city: str = "perm") -> AdapterResult:
        url = MV_SEARCH_URL.format(query=quote(query))
        try:
            html = await fetch_html(
                url,
                wait_selector='a[href*="/products/"]',
                wait_timeout_ms=20000,
            )
            products = parse_search_html(html)[:max_per]
            if not products:
                return AdapterResult(self.name, [], ["mvideo: 0 products"])
            return AdapterResult(self.name, products)
        except Exception as e:
            return AdapterResult(self.name, [], [f"mvideo error: {e}"])

    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        return None

    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        try:
            html = await _fetch_mvideo_reviews(product_id, limit)
        except Exception:
            return []
        return _parse_mvideo_reviews(html, product_id, limit)

    async def top_popular(self, category: str, limit: int = 30, city: str = "perm") -> AdapterResult:
        return await self.search(category, max_per=limit, city=city)

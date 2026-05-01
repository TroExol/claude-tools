"""
Capture live samples from each marketplace. Run when adapters break.
Usage: .venv/Scripts/python tests/capture_fixtures.py [wb|yandex|mvideo|citilink|ozon|dns|all]
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

from curl_cffi import requests as cr

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURES.mkdir(exist_ok=True)

QUERY = "телевизор samsung 55"


async def cap_wb():
    """Capture WB via Playwright — intercept the v18 search XHR."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bin.browser import browser_session
    page_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(QUERY)}"
    captured = {"data": None}

    async with browser_session() as (page, _):
        async def on_response(resp):
            u = resp.url
            if "search.wb.ru" in u and "/search?" in u and "v" in u:
                try:
                    body = await resp.text()
                    if body and body.strip().startswith("{"):
                        captured["data"] = body
                except Exception:
                    pass
        page.on("response", on_response)
        await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        try:
            await page.wait_for_selector('[data-card-index]', timeout=20000)
        except Exception:
            pass
        await page.wait_for_timeout(3000)
    if captured["data"]:
        (FIXTURES / "wb-search.json").write_text(captured["data"], encoding="utf-8")
        print(f"WB: captured {len(captured['data'])} bytes")
    else:
        print("WB: no XHR captured")


def cap_yandex():
    url = f"https://market.yandex.ru/search?text={quote(QUERY)}"
    r = cr.get(url, impersonate="chrome124", timeout=20,
               headers={"Accept-Language": "ru-RU,ru;q=0.9"})
    (FIXTURES / "yandex-search.html").write_text(r.text, encoding="utf-8")
    print(f"Я.Маркет: {r.status_code}, {len(r.text)} bytes")


async def cap_mvideo():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bin.browser import browser_session
    url = f"https://www.mvideo.ru/search?q={quote(QUERY)}"
    async with browser_session() as (page, _):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        for sel in ['a[href*="/product/"]', 'mvid-product-card', '[class*="product-mini-card"]']:
            try:
                await page.wait_for_selector(sel, timeout=20000)
                break
            except Exception:
                continue
        await page.wait_for_timeout(3000)
        html = await page.content()
        (FIXTURES / "mvideo-search.html").write_text(html, encoding="utf-8")
        print(f"МВидео: {len(html)} bytes")


async def cap_citilink():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bin.browser import browser_session
    url = f"https://www.citilink.ru/search/?text={quote(QUERY)}"
    async with browser_session() as (page, _):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            await page.wait_for_function(
                """() => {
                    const el = document.querySelector('[data-meta-name="SnippetProductVerticalLayout"]');
                    return el && el.getAttribute('data-meta-product-id');
                }""",
                timeout=25000,
            )
        except Exception:
            pass
        await page.wait_for_timeout(3000)
        html = await page.content()
        (FIXTURES / "citilink-search.html").write_text(html, encoding="utf-8")
        print(f"Ситилинк: {len(html)} bytes")


async def cap_ozon():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bin.browser import browser_session
    url = f"https://www.ozon.ru/search/?text={quote(QUERY)}"
    async with browser_session() as (page, _):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # Wait for actual product tile, not antibot challenge
        for selector in ['[data-widget="searchResultsV2"]', 'div[data-index]', 'a[href*="/product/"]']:
            try:
                await page.wait_for_selector(selector, timeout=15000)
                break
            except Exception:
                continue
        await page.wait_for_timeout(3000)
        html = await page.content()
        (FIXTURES / "ozon-search.html").write_text(html, encoding="utf-8")
        print(f"Ozon: {len(html)} bytes")


async def cap_dns():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bin.browser import browser_session
    url = f"https://www.dns-shop.ru/search/?q={quote(QUERY)}"
    async with browser_session() as (page, _):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            await page.wait_for_selector('a[href*="/product/"]', timeout=25000)
        except Exception:
            pass
        await page.wait_for_timeout(3000)
        html = await page.content()
        (FIXTURES / "dns-search.html").write_text(html, encoding="utf-8")
        print(f"DNS: {len(html)} bytes")


def main(target: str):
    if target in ("wb", "all"): asyncio.run(cap_wb())
    if target in ("yandex", "all"): cap_yandex()
    if target in ("mvideo", "all"): asyncio.run(cap_mvideo())
    if target in ("citilink", "all"): asyncio.run(cap_citilink())
    if target in ("ozon", "all"): asyncio.run(cap_ozon())
    if target in ("dns", "all"): asyncio.run(cap_dns())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")

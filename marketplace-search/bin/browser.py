from __future__ import annotations
import json
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


SKILL_ROOT = Path(__file__).resolve().parent.parent
COOKIES_DIR = SKILL_ROOT / ".cache"
PROFILES_DIR = SKILL_ROOT / ".cache" / "profiles"


# Stealth init script — патчит признаки автоматизации
STEALTH_INIT = """
// navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
// plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [{name: 'Chrome PDF Plugin'}, {name: 'Chrome PDF Viewer'}, {name: 'Native Client'}]
});
// languages
Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US', 'en']});
// chrome object
window.chrome = window.chrome || {runtime: {}};
// permissions
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : originalQuery(parameters);
}
// WebGL vendor
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel(R) UHD Graphics';
    return getParameter.call(this, parameter);
};
"""


def _cookies_path(marketplace: str) -> Path:
    return COOKIES_DIR / f"cookies-{marketplace}.json"


def save_cookies(marketplace: str, cookies: list[dict[str, Any]]) -> None:
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)
    path = _cookies_path(marketplace)
    data = {"saved_at": int(time.time()), "cookies": cookies}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cookies(marketplace: str) -> list[dict[str, Any]]:
    path = _cookies_path(marketplace)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("cookies", [])
    except (json.JSONDecodeError, OSError):
        return []


def cookies_to_dict(cookies: list[dict[str, Any]]) -> dict[str, str]:
    return {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}


@asynccontextmanager
async def browser_session(
    headless: bool = True,
    cookies: list[dict[str, Any]] | None = None,
    profile: str | None = None,
):
    """Async context manager yielding Playwright Page with stealth + optional persistent profile.

    `profile`: marketplace name → use persistent context with .cache/profiles/{profile}/
               (preserves real browser state — cookies, localStorage, fingerprint).
    """
    async with async_playwright() as pw:
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
        ]
        if profile:
            PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            profile_path = PROFILES_DIR / profile
            # channel="chrome" — реальный установленный Chrome (правильный TLS fingerprint)
            # Fallback на bundled Chromium если Chrome не установлен
            try:
                context: BrowserContext = await pw.chromium.launch_persistent_context(
                    str(profile_path),
                    headless=headless,
                    user_agent=ua,
                    locale="ru-RU",
                    args=launch_args,
                    viewport={"width": 1920, "height": 1080},
                    channel="chrome",
                )
            except Exception:
                context = await pw.chromium.launch_persistent_context(
                    str(profile_path),
                    headless=headless,
                    user_agent=ua,
                    locale="ru-RU",
                    args=launch_args,
                    viewport={"width": 1920, "height": 1080},
                )
            await context.add_init_script(STEALTH_INIT)
            if cookies:
                try:
                    await context.add_cookies(cookies)
                except Exception:
                    pass
            page = context.pages[0] if context.pages else await context.new_page()
            try:
                yield page, context
            finally:
                await context.close()
        else:
            browser: Browser = await pw.chromium.launch(headless=headless, args=launch_args)
            context = await browser.new_context(user_agent=ua, locale="ru-RU",
                                                viewport={"width": 1920, "height": 1080})
            await context.add_init_script(STEALTH_INIT)
            if cookies:
                try:
                    await context.add_cookies(cookies)
                except Exception:
                    pass
            page = await context.new_page()
            try:
                yield page, context
            finally:
                await context.close()
                await browser.close()


async def warmup_and_save_cookies(
    marketplace: str,
    url: str,
    *,
    headless: bool = False,
    wait_ms: int = 60000,
) -> None:
    """Headful warmup using persistent profile. Profile сохранится в .cache/profiles/{marketplace}/.

    После первого прохода antibot challenge profile содержит решённые cookies +
    реальный browser fingerprint. Headless fetch_html использует тот же profile и
    проходит antibot прозрачно.
    """
    async with browser_session(headless=headless, profile=marketplace) as (page, context):
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(wait_ms)
        cookies = await context.cookies()
        save_cookies(marketplace, cookies)


async def fetch_html_via_cdp(
    url: str,
    cdp_endpoint: str,
    *,
    wait_selector: str | None = None,
    wait_function: str | None = None,
    wait_timeout_ms: int = 25000,
    extra_wait_ms: int = 2000,
    paginate: dict | None = None,
) -> str:
    """Fetch via real user Chrome connected over CDP. Bypasses antibot.

    `paginate`: optional dict {item_selector, target_count, max_clicks,
                load_more_selector | scroll_to_bottom, wait_after_ms}
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if wait_function:
                try:
                    await page.wait_for_function(wait_function, timeout=wait_timeout_ms)
                except Exception:
                    pass
            elif wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=wait_timeout_ms)
                except Exception:
                    pass
            await page.wait_for_timeout(extra_wait_ms)
            if paginate:
                await _paginate(page, paginate)
            return await page.content()
        finally:
            await page.close()


async def _paginate(page, opts: dict) -> None:
    """Paginate page by clicking load-more or scrolling until target_count items exist
    or max_clicks reached. opts: item_selector, target_count, max_clicks,
    load_more_selector (optional), scroll_to_bottom (bool), wait_after_ms."""
    item_sel = opts["item_selector"]
    target = opts.get("target_count", 50)
    max_clicks = opts.get("max_clicks", 10)
    load_more = opts.get("load_more_selector")
    scroll_bottom = opts.get("scroll_to_bottom", False)
    wait_after = opts.get("wait_after_ms", 1500)

    for _ in range(max_clicks):
        count = await page.locator(item_sel).count()
        if count >= target:
            break
        if load_more:
            try:
                btn = page.locator(load_more).first
                if await btn.is_visible(timeout=2000):
                    await btn.scroll_into_view_if_needed()
                    await btn.click(timeout=3000)
                else:
                    if scroll_bottom:
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    else:
                        break
            except Exception:
                if scroll_bottom:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                else:
                    break
        elif scroll_bottom:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        else:
            break
        await page.wait_for_timeout(wait_after)


async def fetch_html(
    url: str,
    *,
    wait_selector: str | None = None,
    wait_function: str | None = None,
    wait_timeout_ms: int = 25000,
    extra_wait_ms: int = 2000,
    use_cookies_for: str | None = None,
    use_profile: str | None = None,
    cdp_endpoint: str | None = None,
    paginate: dict | None = None,
) -> str:
    """Fetch fully rendered HTML via Playwright. Stealth init script always applied.

    `cdp_endpoint`: connect to real user Chrome over CDP (bypasses antibot).
                    If env var MARKETPLACE_CDP_URL set, used as default.
    `use_profile`: persistent context profile (preferred for antibot — Ozon/DNS).
    `use_cookies_for`: just preload cookies (for non-persistent flows).
    `paginate`: pagination opts (см. _paginate).
    """
    import os
    cdp = cdp_endpoint or os.environ.get("MARKETPLACE_CDP_URL")
    if cdp:
        return await fetch_html_via_cdp(
            url, cdp,
            wait_selector=wait_selector, wait_function=wait_function,
            wait_timeout_ms=wait_timeout_ms, extra_wait_ms=extra_wait_ms,
            paginate=paginate,
        )
    cookies = load_cookies(use_cookies_for) if use_cookies_for else None
    async with browser_session(cookies=cookies, profile=use_profile) as (page, _):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if wait_function:
            try:
                await page.wait_for_function(wait_function, timeout=wait_timeout_ms)
            except Exception:
                pass
        elif wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=wait_timeout_ms)
            except Exception:
                pass
        await page.wait_for_timeout(extra_wait_ms)
        return await page.content()

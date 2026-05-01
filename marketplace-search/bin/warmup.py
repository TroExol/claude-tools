#!/usr/bin/env python
"""
Headful warmup script для Ozon/DNS.

Открывает браузер, юзер вручную проходит antibot challenge (одноразово),
cookies сохраняются в .cache/cookies-{marketplace}.json.

Usage:
    .venv/Scripts/python bin/warmup.py ozon
    .venv/Scripts/python bin/warmup.py dns
    .venv/Scripts/python bin/warmup.py all
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bin.browser import warmup_and_save_cookies


URLS = {
    "ozon": "https://www.ozon.ru/search/?text=телевизор",
    "dns":  "https://www.dns-shop.ru/search/?q=телевизор",
}


async def warmup(marketplace: str, wait_seconds: int = 60) -> None:
    url = URLS[marketplace]
    print(f"\n=== {marketplace.upper()} warmup ===")
    print(f"URL: {url}")
    print(f"Браузер откроется headful. У тебя {wait_seconds}s чтобы:")
    print(f"  1. Дождаться прохождения antibot challenge")
    print(f"  2. Если потребуется — нажать 'Я не робот' / выбрать картинки")
    print(f"  3. Дождаться загрузки страницы с товарами")
    print(f"После {wait_seconds}s cookies сохранятся в .cache/cookies-{marketplace}.json\n")
    await warmup_and_save_cookies(marketplace, url, headless=False, wait_ms=wait_seconds * 1000)
    print(f"OK: {marketplace} cookies saved")


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    targets = ["ozon", "dns"] if target == "all" else [target]
    for m in targets:
        if m not in URLS:
            print(f"Unknown: {m}. Available: {list(URLS.keys())}")
            continue
        await warmup(m, wait)


if __name__ == "__main__":
    asyncio.run(main())

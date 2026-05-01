# Marketplace-Search Skill — Implementation Status

**Last updated:** 2026-04-30 (session 6 — 6/6 live via CDP)

## Snapshot

**🎉 6/6 live working.** Все маркетплейсы возвращают реальные товары. Ozon/DNS antibot обойден через CDP к реальному Chrome пользователя.

**Verified:**
```
wb       count=3 ok=True   (curl_cffi v18 endpoint)
yandex   count=3 ok=True   (CDP fetch)
mvideo   count=3 ok=True   (CDP fetch)
citilink count=3 ok=True   (CDP fetch)
ozon     count=3 ok=True   (CDP — bypass antibot)
dns      count=3 ok=True   (CDP — bypass Qrator)
```

22/22 offline tests PASS.

## Setup для live (CDP)

**Зачем:** Ozon/DNS top-tier antibot блокирует Playwright + stealth + persistent profile + system Chrome. Реальный Chrome пользователя через CDP проходит т.к. имеет настоящий TLS fingerprint, cookies, history.

```bash
# 1. Запустить Chrome с debug port (любой профиль; новый user-data-dir чтобы не конфликтовать с обычным Chrome)
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-debug-profile"

# 2. Helper использует CDP когда установлен env var
MARKETPLACE_CDP_URL=http://localhost:9222 \
  .venv/Scripts/python bin/helper.py search \
    --query "<query>" \
    --marketplaces all \
    --max-per 30
```

Без `MARKETPLACE_CDP_URL` — fallback на Playwright Chromium с stealth init (4/6 работают: WB+Yandex+MVideo+Citilink, Ozon/DNS вернут antibot error).

## Done

| Task | Status |
|------|--------|
| 1-6: Scaffolding/deps/dataclasses/http_client/browser/capture | ✅ |
| 7: WB adapter | ✅ v18 endpoint |
| 8: Я.Маркет adapter | ✅ DOM productSnippet |
| 9: МВидео adapter | ✅ DOM /products/ |
| 10: Ситилинк adapter | ✅ DOM SnippetProductVerticalLayout |
| 11: Ozon adapter | ✅ via CDP |
| 12: DNS adapter | ✅ via CDP |
| 13: normalizer | ✅ |
| 14: ranker | ✅ search+discover |
| 15: orchestrator | ✅ async fan-out |
| 16: helper.py CLI | ✅ |
| 17: SKILL.md | ✅ |
| 18-21: references/* | ✅ |
| 22: integration smoke | ✅ |

## Файловая структура

```
~/.claude/skills/marketplace-search/
├── SKILL.md                       # ✅ orchestration + CDP setup
├── STATUS.md                      # этот файл
├── conftest.py
├── bin/
│   ├── http_client.py             # curl_cffi factory
│   ├── browser.py                 # Playwright + stealth + CDP fallback
│   ├── warmup.py                  # headful warmup для persistent profile
│   ├── normalizer.py              # ✅
│   ├── ranker.py                  # ✅ search + discover
│   ├── orchestrator.py            # ✅ async fan-out
│   ├── helper.py                  # ✅ CLI (читает MARKETPLACE_CDP_URL)
│   ├── requirements.txt
│   └── marketplaces/
│       ├── base.py
│       ├── wb.py                  # ✅ v18 endpoint (curl_cffi)
│       ├── yandex_market.py       # ✅ DOM productSnippet
│       ├── mvideo.py              # ✅ DOM /products/ (Playwright/CDP)
│       ├── citilink.py            # ✅ DOM SnippetProductVertical (Playwright/CDP)
│       ├── ozon.py                # ✅ DOM (CDP only — antibot)
│       └── dns.py                 # ✅ DOM (CDP only — Qrator)
├── references/                    # 4 docs
└── tests/                         # 22 PASS offline
    ├── capture_fixtures.py
    └── fixtures/
        ├── wb-search.json
        ├── yandex-search.html     # 2.5MB real SSR
        ├── mvideo-search.html     # 307KB Playwright
        ├── citilink-search.html   # 502KB Playwright
        ├── ozon-search.html       # 798KB CDP (real Chrome)
        └── dns-search.html        # ?KB Qrator-blocked (CDP works at runtime)
```

## Tests

```bash
cd ~/.claude/skills/marketplace-search
.venv/Scripts/pytest tests/ -v -k "not live_smoke and not test_full_search"
```
22 PASSED, 5 deselected (live tests требуют network/CDP).

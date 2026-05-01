# Marketplaces Reference

Точные эндпоинты, квирки и стратегии. Обновлять при поломках адаптеров.

## 1. WB (Wildberries) — ✅ работает

- **Tier:** 1 (HTTP curl_cffi)
- **Search v18:** `https://search.wb.ru/exactmatch/ru/common/v18/search?appType=1&curr=rub&dest=-1257786&lang=ru&page=1&query={q}&resultset=catalog&sort=popular&spp=30`
- **Reviews:** `https://feedbacks{1|2}.wb.ru/feedbacks/v2/{nm_id}` (shard зависит от nm_id)
- **Product URL:** `https://www.wildberries.ru/catalog/{nm_id}/detail.aspx`
- **Price:** `sizes[0].price.product` (текущая, копейки), `sizes[0].price.basic` (старая)
- **Quirks:**
  - `dest=-1257786` — Пермь
  - При популярных категорийных запросах v18 возвращает preset-redirect — нужно следовать (пока не реализовано)
  - Rate-limit 429 при частых запросах с одного IP, ~10 минут охлаждение

## 2. Ozon — ⚠️ stub

- **Tier:** 2 (Playwright + cookie reuse)
- **Search:** `https://www.ozon.ru/search/?text={q}` (HTML SSR)
- **Antibot:** Qrator + JS challenge → "Доступ ограничен" page без cookies
- **Quirks:**
  - Первый запрос → 403 + Antibot Challenge Page
  - Playwright решает challenge → cookies сохраняются → дальше HTTP
  - Cookies живут несколько часов

## 3. Я.Маркет — ✅ работает (DOM)

- **Tier:** 1 (HTTP curl_cffi)
- **Search:** `https://market.yandex.ru/search?text={q}` (HTML SSR)
- **Cards:** `[data-zone-name="productSnippet"]` (~19 карточек на странице)
- **Selectors:** `[data-auto="snippet-title"]`, `[data-auto="snippet-price-current"]`, `[data-auto="reviews"]`
- **URL:** `/card/{slug}/{id}` — последний segment = product id
- **Antibot:** SmartCaptcha (HTTP 429 / редирект на `/showcaptcha`)
- **Quirks:**
  - `__NEXT_DATA__` отсутствует — только DOM parsing
  - При капче — площадка отбрасывается

## 4. DNS — ⚠️ stub

- **Tier:** 2 (Playwright + cookie reuse)
- **Search:** `https://www.dns-shop.ru/search/?q={q}`
- **Antibot:** Qrator (HTTP 403 + `__qrator` script)
- **Cookies:** `qrator_jsr`, `qrator_jsid`, `qrator_ssid`

## 5. МВидео — ⚠️ stub

- **Tier:** 2 (Playwright — Angular SPA)
- **Search:** `https://www.mvideo.ru/search?q={q}`
- **Quirks:** SSR пустой (`<mvid-root></mvid-root>`), цены и карточки — JS-рендер. Нужен Playwright

## 6. Ситилинк — ⚠️ stub

- **Tier:** 2 (Playwright — lazy hydrate)
- **Search:** `https://www.citilink.ru/search/?text={q}`
- **State:** `<script id="__NEXT_DATA__">` есть, но карточки в `[data-meta-name="SnippetProductVerticalLayout"]` skeleton-loaded (`data-meta-product-id=""` пустой)
- **Quirks:** реальные данные только после client hydration → нужен Playwright + wait

## Capture фикстур

```bash
.venv/Scripts/python tests/capture_fixtures.py [wb|yandex|mvideo|citilink|ozon|dns|all]
```

WB и Я.Маркет — HTTP. Остальные — Playwright (`tests/capture_fixtures.py` уже настроен с wait_for_selector).

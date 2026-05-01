---
name: marketplace-search
description: >
  Поиск товаров и отзывов на 6 RU-маркетплейсах (Wildberries, Ozon, Яндекс Маркет, DNS, МВидео, Ситилинк).
  Два режима: search (конкретная модель — найти + отзывы) и discover (категория → веб-топы → шортлист → ранжирование).
  Триггеры: "найди", "сравни", "подбери лучший", "что выбрать", "топ X", "какой купить", "посоветуй".
---

# Marketplace-Search

Скилл агрегирует данные о товарах с 6 RU-маркетплейсов через Python-helper и выдаёт ранжированные результаты с отзывами. Цены — не главный фокус (для дешёвых офферов используется yoloprice).

**Текущий статус адаптеров:**
- ✅ Search (все 6): WB (curl_cffi v18), Я.Маркет/MVideo/Citilink (Playwright DOM), Ozon/DNS (CDP)
- ✅ Reviews: WB/Ozon/DNS/MVideo (4/6). Yandex/Citilink — TODO

## Шаг 0: Установка (первый запуск)

Если `.venv/` отсутствует:

```bash
cd ~/.claude/skills/marketplace-search
python -m venv .venv
.venv/Scripts/pip install -r bin/requirements.txt
.venv/Scripts/playwright install chromium
```

## Шаг 0.5: CDP auto-setup (для Ozon/DNS antibot bypass)

Ozon/DNS блокируют Playwright+stealth — нужен реальный Chrome через CDP. **Запускать вручную не надо** — `bin/ensure_chrome.py` стартует Chrome в background если не запущен.

**Перед каждым запуском helper'а** делай:
```bash
CDP_URL=$(.venv/Scripts/python bin/ensure_chrome.py)
export MARKETPLACE_CDP_URL=$CDP_URL
```

`ensure_chrome.py` проверяет `http://localhost:9222/json/version`, если не отвечает — запускает Chrome detached в background (`--user-data-dir=~/chrome-debug-profile`), ждёт до 30s готовности, печатает CDP URL на stdout. На второй и далее запуски Chrome уже есть → мгновенно.

Без CDP: WB+Yandex+MVideo+Citilink работают, Ozon/DNS вернут antibot error.

**Авторизация для лучших цен:** один раз залогинься в окне Chrome (Ozon Karta, OZON ID и т.д.) — цены далее идут с учётом бонусов/программ лояльности. Профиль persistent.

## Гочи скилла

- **Strict-mode:** при поиске точной модели (например "TCL 55C8L") добавляй `--strict` к helper'у — отфильтровывает соседние модели (55C6K, 55C7L), оставляя только те где все токены query >=3 chars в title.
- **Цены и бонусы:** все адаптеры возвращают `price` в копейках (int). MVideo доп. в `raw.bonus` — рублей бонусов (не вычитать из цены). При выводе делить на 100.
- **Subagent stalled:** если subagent не отвечает >300s — retry с тем же промптом, не оставляй пробел.
- **/tmp на Windows:** не использовать `/tmp` напрямую. Бери `tempfile.gettempdir()` или `os.environ['TEMP']`.
- **Reviews:** через helper.py доступны для WB (feedbacks API), Ozon (CDP scroll), DNS (CDP "Показать ещё" pagination), MVideo (5 отзывов в карусели на product page). Yandex/Citilink — TODO (Yandex CSR рендерит отзывы только в реальном профиле, через CDP пустые `<div></div>`). Subagents review-summary запускать для wb/ozon/dns/mvideo, остальные пропускать.

## Шаг 1: Парсинг запроса

Извлеки из сообщения:

| Параметр | Обязательность | Как искать |
|----------|---------------|------------|
| **mode** | авто-детект | "найди/сравни/где купить/посмотри отзывы" → `search`; "подбери/что выбрать/топ/посоветуй" → `discover` |
| **query** или **category** | обязательно | основной предмет поиска |
| **budget** | опционально | "до", "не дороже", "бюджет", "максимум" |
| **brand** | опционально | известные бренды в запросе |
| **city** | опционально (default: Perm) | "в Москву" → Москва |
| **requirements** | опц. (discover) | технические требования |

Если query/category неоднозначно — спросить. Не угадывай.

## Шаг 2 (search-mode)

1. **Query expansion** — 2-3 варианта (точный, синонимы, английский)
2. **Helper call:**
   ```bash
   .venv/Scripts/python bin/helper.py search \
     --query "<query>" \
     --marketplaces all \
     --max-per 30 \
     --city <city>
   ```
   JSON: `{"products": [...], "errors": [...], "stats": {...}}`
3. **Дедуп:** один товар на разных площадках → оставить ВСЕ (сравнение цен). Helper уже дедуплицирует внутри площадки
4. **Subagents review-summary** (опционально, до 5 параллельно): топ-5 по предварительному скору → spawn sonnet с промптом из `references/subagent-prompts.md`
5. **Ранжирование** — `bin/ranker.py rank_search_mode`
6. **Output формат** — секция «Output: search-mode»

## Шаг 2 (discover-mode)

1. **Уточнения** (до 5): бюджет, требования, бренд, размер/мощность, сценарий. "Не важно" — принять
2. **Subagent: веб-ресёрч топов** (1, sonnet) — промпт из `references/subagent-prompts.md`
3. **Helper:** ищем шортлист + категорийный топ
   ```bash
   for model in shortlist:
       helper.py search --query "<model>" --marketplaces all
   helper.py top-popular --category "<seed>" --marketplaces wb,yandex
   ```
4. **Subagents review-summary** (до 5 параллельно) для топ-5
5. **Кросс-валидация:** в шортлисте + высокий рейтинг = сильный сигнал
6. **Ранжирование:** `rank_discover_mode(products, expert_models=shortlist_dict, budget=...)`
7. **Output формат** — секция «Output: discover-mode»

## Output: search-mode

```
## 🛒 {query}

Найдено на {N}/6 маркетплейсах, проанализировано {M} товаров.
{⚠️ Не удалось получить с: {список}}

### 1. {Название}
📍 {Площадка} | 💰 {цена}₽ {~~{старая}₽~~ если скидка}
⭐ {rating} ({reviews} отзывов) | 🚚 {delivery}
🔗 {url}
💡 {Почему в топе}
{👍 Плюсы / 👎 Минусы — если есть review-summary}

### 2. ... (до 13)
```

Цены с пробелом: `15 990₽`. Рейтинг — одна десятичная: `4.7`. Доставка — `Завтра`/`2-3 дня`/`5 дней`. Нет отзывов → "нет отзывов".

## Output: discover-mode

```
## 🔍 Подбор: {категория}

📊 Проанализировано {M} товаров на {N}/6 маркетплейсах.
{⚠️ Не удалось: {список}}

### 📋 На что обращать внимание
{2-4 ключевых критерия из веб-ресёрча}

---

### 🥇 Рекомендация #1: {Модель}
{Почему: эксперты + народный рейтинг}
{Соответствие требованиям}

Цены и наличие:
• {Площадка} — {цена}₽ (⭐{rating}, {reviews} отзывов) 🏆
• ...

👍 Плюсы из отзывов: {3-5}
👎 Минусы из отзывов: {3-5}

---

### 🥈 Рекомендация #2: ...
### 🥉 Рекомендация #3: ...

---

### 🏅 Также стоит рассмотреть
**{Модель 4}** — {описание, цена от X₽}
**{Модель 5}** — ...

---

### 💡 Вердикт
{Итог. Если явный лидер — назвать. Иначе — описать когда что брать.}
```

## Обработка ошибок

| Ситуация | Действие |
|----------|----------|
| Helper падает с ImportError | `pip install -r bin/requirements.txt` |
| Все 6 площадок fail | Сообщить, спросить уточнение |
| Часть площадок fail | Продолжить с остальными, упомянуть пропуски |
| stub-адаптер вернул "not implemented" | Просто пропустить эту площадку |
| Playwright cookies истекли | Helper рефрешит автоматически |
| SmartCaptcha на Я.Маркет | Площадка вернёт error — продолжить без неё |

## Файлы-референсы

- `references/marketplaces.md` — эндпоинты и квирки
- `references/helper-cli.md` — CLI спека
- `references/trust-signals.md` — детектор продажности веб-топов
- `references/subagent-prompts.md` — промпты для subagents

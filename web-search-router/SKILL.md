---
name: web-search-router
description: Авто-роутинг веб-поиска между провайдерами Serper (Google), Tavily (research/docs) и Exa (семантический/код). Активируется когда нужен веб-поиск, поиск документации, исследование темы, извлечение контента со страниц, или краулинг сайта.
user-invocable: false
disable-model-invocation: false
---

# Web Search Router

Интеллектуальный роутинг между тремя поисковыми MCP-провайдерами.

---

## Доступные провайдеры и инструменты

### Serper (Google Search API)
| Инструмент | Назначение |
|---|---|
| `mcp__serper-search__google_search` | Поиск Google с операторами (site:, filetype:, inurl:, intitle:, before:, after:, exact:, exclude:) |
| `mcp__serper-search__scrape` | Извлечение контента страницы |

### Tavily
| Инструмент | Назначение |
|---|---|
| `mcp__tavily-remote-mcp__tavily_search` | Быстрый веб-поиск с фильтрами по дате, стране, домену, глубине |
| `mcp__tavily-remote-mcp__tavily_skill` | Поиск документации библиотек/API (передаёшь library, language, task) |
| `mcp__tavily-remote-mcp__tavily_research` | Глубокое мульти-источниковое исследование (mini/pro) |
| `mcp__tavily-remote-mcp__tavily_extract` | Извлечение контента из URL (advanced для LinkedIn и защищённых сайтов) |
| `mcp__tavily-remote-mcp__tavily_crawl` | Краулинг сайта с настройкой глубины и ширины |
| `mcp__tavily-remote-mcp__tavily_map` | Карта сайта — список URL без контента |

### Exa (Neural/Semantic Search)
| Инструмент | Назначение |
|---|---|
| `mcp__exa__web_search_exa` | Семантический поиск — описываешь идеальную страницу словами, не ключевыми словами |
| `mcp__exa__get_code_context_exa` | Поиск примеров кода, документации, решений по программированию |
| `mcp__exa__crawling_exa` | Чтение полного контента по URL (батчевое) |

---

## Матрица роутинга

| Я хочу... | Инструмент | Пример запроса |
|---|---|---|
| Найти цену товара, магазин | Serper `google_search` | "iPhone 16 Pro Max цена" |
| Найти ресторан/сервис рядом | Serper `google_search` | "лучшая пицца рядом" |
| Использовать Google-операторы | Serper `google_search` | "site:habr.com React hooks" |
| Найти конкретный тип файла | Serper `google_search` | "filetype:pdf React architecture" |
| Проверить SEO-позиции в Google | Serper `google_search` | "мой-сайт.ru ключевое слово" |
| Поиск по российской/локальной выдаче | Serper `google_search` (gl=ru) | Любой запрос с региональным контекстом |
| Быстро узнать факт/новость | Tavily `tavily_search` | "курс доллара сегодня" |
| Поиск с фильтром по дате | Tavily `tavily_search` | "React 19 новости за последний месяц" |
| Понять как что-то работает | Tavily `tavily_search` (advanced) | "как работает HTTPS шифрование" |
| Глубоко исследовать тему | Tavily `tavily_research` | "сравнение архитектур микросервисов" |
| Найти документацию библиотеки | Tavily `tavily_skill` | "Next.js App Router SSR streaming" |
| Найти API/SDK документацию | Tavily `tavily_skill` | "Prisma relations many-to-many" |
| Извлечь контент с LinkedIn | Tavily `tavily_extract` (advanced) | URL LinkedIn-профиля или поста |
| Обойти и проиндексировать сайт | Tavily `tavily_crawl` | URL сайта для обхода |
| Получить карту URL сайта | Tavily `tavily_map` | URL корневой страницы |
| Найти "компании/стартапы как X" | Exa `web_search_exa` | "стартапы похожие на Notion" |
| Найти статью по описанию | Exa `web_search_exa` | "блог-пост сравнивающий React и Vue по перформансу" |
| Найти научные статьи/papers | Exa `web_search_exa` | "transformer architecture research papers" |
| Найти примеры кода | Exa `get_code_context_exa` | "Python requests POST with JSON body" |
| Найти решение бага | Exa `get_code_context_exa` | "TypeScript Cannot find module error ESM" |
| Прочитать контент страницы по URL | Exa `crawling_exa` / Tavily `tavily_extract` | Любой URL |

---

## Логика принятия решения

```
1. Есть конкретная библиотека/API? → tavily_skill
2. Нужен глубокий ресёрч из множества источников? → tavily_research
3. Нужны Google-операторы (site:, filetype:, и т.д.)? → Serper
4. SEO-анализ или позиции в Google? → Serper
5. Локальный/региональный поиск (рядом, в городе)? → Serper
6. Цены, товары, шоппинг? → Serper
7. Примеры кода или решение бага? → exa get_code_context
8. Семантический запрос "найди похожее на..."? → exa web_search
9. Научные статьи, papers? → exa web_search
10. Новости с фильтром по дате? → tavily_search
11. Нужно прочитать страницу по URL? → exa crawling (батч) или tavily_extract (protected sites)
12. Нужно обойти/проиндексировать сайт? → tavily_crawl
13. Всё остальное → tavily_search (самый универсальный)
```

---

## Сравнение провайдеров

| Характеристика | Serper | Tavily | Exa |
|---|---|---|---|
| Скорость | Быстрый | Средний | Средний |
| Google-операторы | Да | Нет | Нет |
| Семантический поиск | Нет | Частично | Да |
| Поиск кода | Нет | tavily_skill | get_code_context |
| Глубокий ресёрч | Нет | tavily_research | Нет |
| Краулинг сайта | Нет | tavily_crawl/map | Нет |
| Фильтр по дате | tbs параметр | start_date/end_date | freshness |
| Региональность | gl + hl | country | Нет |
| Контент страницы | scrape | extract (advanced) | crawling (батч) |
| Защищённые сайты | Нет | extract advanced | Нет |
| Документация | Нет | tavily_skill | get_code_context |

---

## Важные нюансы

- **Exa web_search**: запрос должен описывать идеальную страницу, а НЕ быть набором ключевых слов. "Блог-пост про оптимизацию React рендеринга", а не "React optimization"
- **Serper**: обязательные параметры `gl` и `hl` — всегда указывай регион и язык
- **Tavily skill**: передавай `library` когда знаешь конкретную библиотеку — это сужает поиск
- **Tavily research**: используй `mini` для узких тем, `pro` для широких
- **Tavily extract**: используй `advanced` для LinkedIn, защищённых сайтов и таблиц
- **Exa crawling**: поддерживает батчевое чтение нескольких URL за один вызов
- **Fallback**: если провайдер не дал результат, попробуй другой из таблицы роутинга

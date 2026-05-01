# Helper CLI Spec

Все вызовы запускают helper в venv. Output — JSON на stdout.

## search

```bash
.venv/Scripts/python bin/helper.py search \
    --query "Samsung QE55Q60D" \
    --marketplaces all \
    --max-per 30 \
    --city perm \
    --timeout 60
```

**Output:**
```json
{
  "products": [
    {
      "marketplace": "wb",
      "marketplace_product_id": "12345",
      "title": "Телевизор Samsung QE55Q60D",
      "price": 4990000,
      "old_price": 5990000,
      "rating": 4.8,
      "reviews_count": 1234,
      "url": "https://www.wildberries.ru/catalog/12345/detail.aspx",
      "image_url": "...",
      "delivery": null,
      "in_stock": true,
      "raw": { "...": "..." }
    }
  ],
  "errors": [
    { "marketplace": "ozon", "errors": ["ozon adapter stub: ..."] }
  ],
  "stats": {
    "wb": { "count": 28, "ok": true },
    "ozon": { "count": 0, "ok": false }
  }
}
```

## top-popular

```bash
.venv/Scripts/python bin/helper.py top-popular \
    --category "телевизор 55 4К" \
    --marketplaces wb,ozon,yandex \
    --limit 20 \
    --city perm
```

Same output schema as search.

## reviews

```bash
.venv/Scripts/python bin/helper.py reviews \
    --marketplace wb \
    --product-id 12345 \
    --limit 50
```

**Output:**
```json
{
  "reviews": [
    {
      "marketplace": "wb",
      "product_id": "12345",
      "rating": 5,
      "text": "Отличный телевизор...",
      "author": "Иван",
      "date": "2026-04-01",
      "pros": "Картинка",
      "cons": "Звук",
      "helpful_count": null
    }
  ]
}
```

## product

```bash
.venv/Scripts/python bin/helper.py product \
    --marketplace wb \
    --product-id 12345 \
    --city perm
```

**Output:** `{ "product": { ...Product... } | null }`

## Аргументы

| Аргумент | Тип | Default | Где |
|----------|-----|---------|-----|
| `--marketplaces` | csv \| `all` | `all` | search, top-popular |
| `--max-per` | int | 30 | search |
| `--limit` | int | 30/50 | top-popular, reviews |
| `--city` | str | `perm` | search, product, top-popular |
| `--timeout` | int (сек) | 60 | search, top-popular |

## Цена в копейках

`price` и `old_price` — в копейках (int). В рублях: `price // 100`.

# Subagent Prompts

Шаблоны для спавна субагентов из главного скилла. Все subagents — sonnet.

## 1. Web research tops (discover-mode)

**Когда:** сразу после уточнений в discover-mode.
**Кол-во:** 1 subagent.
**Модель:** sonnet.

**Промпт-шаблон:**

```
Ты собираешь шортлист моделей для категории "{category}" с бюджетом до {budget}₽ и требованиями: {requirements}.

Используй skill `web-search-router` для следующих запросов:
1. "Лучшие {category} 2026 рейтинг"
2. "Как выбрать {category} на что обратить внимание"
3. "Топ {category} до {budget}₽"
4. "{category} сравнение обзор"
{если есть requirements: 5. "{category} {requirements}"}

Фетчи 2-3 топ-статей через тот же skill.

Применяй правила из `~/.claude/skills/marketplace-search/references/trust-signals.md` к каждой статье — выдавай confidence-score 0..1.

Верни структурированный JSON-блок:

{
  "criteria": [
    "Краткий критерий выбора 1",
    "Краткий критерий выбора 2"
  ],
  "shortlist": [
    { "model": "Полное название модели", "confidence": 0.85, "why": "почему рекомендуют" }
  ]
}

5-7 моделей в shortlist. Confidence — взвешенный score из trust-signals.
```

## 2. Review summary (search и discover modes)

**Когда:** для каждой из топ-5 моделей по пред-скору.
**Кол-во:** до 5 параллельно.
**Модель:** sonnet.

**Промпт-шаблон:**

```
Тебе нужно собрать саммари отзывов на товар.

1. Запусти:
   `~/.claude/skills/marketplace-search/.venv/Scripts/python ~/.claude/skills/marketplace-search/bin/helper.py reviews --marketplace {marketplace} --product-id {product_id} --limit 50`

2. Прочитай JSON. Если отзывов <5 — верни:
   { "summary": null, "pros": [], "cons": [], "rating_distribution": null }

3. Если отзывов достаточно:
   - Краткое summary 2-3 предложения
   - Плюсы (3-5 пунктов) — что хвалят чаще
   - Минусы (3-5 пунктов) — на что жалуются
   - Распределение оценок: {5: N, 4: N, 3: N, 2: N, 1: N}

Верни JSON:
{
  "summary": "2-3 предложения",
  "pros": ["...", "..."],
  "cons": ["...", "..."],
  "rating_distribution": { "5": 120, "4": 30, "3": 5, "2": 2, "1": 1 }
}

Не выдумывай. Только из отзывов.
```

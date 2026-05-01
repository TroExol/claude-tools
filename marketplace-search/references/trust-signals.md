# Trust Signals — Web Tops Detector

Используется subagent'ом веб-ресёрча в discover-mode для оценки доверия к статьям-топам. Каждой статье присваивается confidence-score 0..1, далее score применяется как вес экспертного сигнала.

## Базовый score = 0.5

## Положительные сигналы (поднимают score)

| Сигнал | Вес | Как проверить |
|--------|-----|---------------|
| Возраст домена >5 лет | +0.20 | whois / archive.org wayback |
| Указан автор с био и фото | +0.15 | DOM проверка `<author>`, ссылка на профиль |
| Ссылки на лабораторные тесты | +0.15 | rtings.com, displayspecifications.com, ixbt.com тесты |
| Упоминание на YouTube тест-каналах | +0.15 | поиск названия модели + YouTube |
| Кросс-цитирование между статьями (>2) | +0.10 | модель упомянута в нескольких независимых топах |

## Отрицательные сигналы (понижают score)

| Сигнал | Вес | Как проверить |
|--------|-----|---------------|
| Партнёрские reflinks (`?ref=`, `?aff_id=`, `goto.ozon.ru`, `clck.ru`, `wbo`) | -0.30 | regex по href |
| Домен <1 года | -0.20 | whois |
| Нет авторов / только "редакция" | -0.10 | DOM |
| Идентичный контент на 5+ сайтах | -0.20 | Google поиск точной фразы |
| Только маркетплейс-ссылки, нет независимых обзоров | -0.15 | подсчёт ссылок |

## Алгоритм

```
score = 0.5
for signal in positive_signals:
    if signal.applies():
        score += signal.weight
for signal in negative_signals:
    if signal.applies():
        score += signal.weight  # отрицательные
score = max(0.0, min(1.0, score))
```

## Применение

Возвращаемый shortlist:
```python
[
    {"model": "Samsung QE55QN90D", "confidence": 0.85},
    {"model": "LG OLED55C4", "confidence": 0.78},
    {"model": "Hisense 55U7N", "confidence": 0.40},  # партнёрские топы
]
```

Confidence передаётся в `rank_discover_mode(expert_models={...})` и умножается на 0.25 в финальной формуле.

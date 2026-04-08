# Claude Code Tools

Коллекция скиллов, плагинов и MCP-серверов для [Claude Code](https://code.claude.com/docs).

## Skills

> Skills — это набор готовых инструкций, которые учат Claude Code выполнять конкретную задачу нужным способом.

| Скилл | Описание |
|-------|----------|
| [web-search-router](./web-search-router) | Авто-роутинг веб-поиска между провайдерами: Serper (Google), Tavily (research/docs) и Exa (семантический/код). |
| [composition-patterns](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns) | React composition patterns: compound components, render props, context providers. Включает React 19 API. |
| [react-best-practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | Гайдлайны оптимизации React и Next.js от Vercel Engineering: производительность, data fetching, bundling. |
| [web-design-guidelines](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines) | Ревью UI-кода на соответствие Web Interface Guidelines: доступность, UX, лучшие практики. |
| [grill-me](https://github.com/mattpocock/skills/blob/main/grill-me) | Интервьюер для стресс-тестирования планов и дизайн-решений — вопросы по каждой ветви дерева решений. |
| [readme-generator](https://github.com/serejaris/ris-claude-code/tree/main/skills/readme-generator) | Генерация README.md: исследование best practices, анализ структуры проекта, human-focused документация. |
| [marketingskills](https://github.com/coreyhaines31/marketingskills) | Набор из 35+ скиллов для маркетинга: CRO, копирайтинг, SEO, аналитика, growth engineering. |

## MCP-серверы

> MCP (Model Context Protocol) серверы расширяют возможности Claude Code, предоставляя доступ к внешним сервисам и инструментам.

| MCP-сервер | Описание |
|------------|----------|
| [`chrome-devtools`](https://claude.com/plugins/chrome-devtools-mcp) | Управление браузером: скриншоты, клики, навигация, DevTools, Lighthouse аудит, трассировка производительности |
| [`context7`](https://claude.com/plugins/context7) | Актуальная документация библиотек и фреймворков прямо в контексте LLM |
| [`exa`](https://exa.ai/docs/reference/exa-mcp#claude-code) | Семантический веб-поиск и извлечение контента |
| [`serper`](https://github.com/marcopesani/mcp-server-serper?tab=readme-ov-file#installing-via-smithery) | Google Search API — веб-поиск и скрейпинг страниц |
| [`tavily`](https://docs.tavily.com/documentation/mcp#connect-to-claude-code) | Исследовательский поиск: crawl, extract, map, research |
| [`figma`](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/#claude-code) | Интеграция с Figma для работы с дизайн-макетами |

## Плагины

> Плагин в Claude Code — это устанавливаемый модуль, который может объединять skills, hooks, subagents и MCP servers.

| Плагин | Описание |
|--------|----------|
| [superpowers](https://claude.com/plugins/superpowers) | Фреймворк агентных скиллов и методология разработки: brainstorming, планирование, TDD, debugging, code review, git worktrees и другое. |
| [code-simplifier](https://claude.com/plugins/code-simplifier) | Агент для упрощения и рефакторинга кода с сохранением функциональности |
| [claude-md-management](https://claude.com/plugins/claude-md-management) | Инструменты для поддержки и улучшения файлов CLAUDE.md |
| [pr-review-toolkit](https://claude.com/plugins/pr-review-toolkit) | Комплексное ревью PR через специализированных агентов |
| [claude-code-setup](https://claude.com/plugins/claude-code-setup) | Анализ кодовой базы и рекомендации по настройке Claude Code |
| [explanatory-output-style](https://claude.com/plugins/explanatory-output-style) | Образовательные инсайты о реализации и паттернах кода |
| [skill-creator](https://claude.com/plugins/skill-creator) | Создание, улучшение и тестирование скиллов |
| [typescript-lsp](https://claude.com/plugins/typescript-lsp) | TypeScript Language Server Protocol — типизация, автокомплит, диагностика |
| [frontend-design](https://claude.com/plugins/frontend-design) | Скилл для создания качественного UI |

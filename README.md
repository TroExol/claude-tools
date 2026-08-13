**English** u{00B7} [u{0420}u{0443}u{0441}u{0441}u{043A}u{0438}u{0439}](./README.ru.md)

# Claude Code Tools

A curated collection of skills, plugins and MCP servers for [Claude Code](https://code.claude.com/docs).

Most entries link out to their upstream authors; `web-search-router` is built here.

## Skills

> Skills are packaged instructions that teach Claude Code to perform a specific task in a specific way.

| Skill | Description |
|-------|-------------|
| [web-search-router](./web-search-router) | Routes web searches automatically between providers: Serper (Google), Tavily (research/docs) and Exa (semantic/code). |
| [composition-patterns](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns) | React composition patterns: compound components, render props, context providers. Covers the React 19 API. |
| [react-best-practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | React and Next.js optimisation guidelines from Vercel Engineering: performance, data fetching, bundling. |
| [web-design-guidelines](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines) | Reviews UI code against the Web Interface Guidelines: accessibility, UX, best practices. |
| [grill-me](https://github.com/mattpocock/skills/blob/main/grill-me) | An interviewer that stress-tests plans and design decisions, working through every branch of the decision tree. |
| [readme-generator](https://github.com/serejaris/ris-claude-code/tree/main/skills/readme-generator) | Generates README.md files: researches best practices, analyses project structure, writes human-focused docs. |
| [marketingskills](https://github.com/coreyhaines31/marketingskills) | 35+ marketing skills: CRO, copywriting, SEO, analytics, growth engineering. |
| [taste-skill](https://github.com/Leonxlnx/taste-skill) | High-agency frontend: sharpens the agent's design taste and pushes back against generic UI slop. |
| [caveman](https://github.com/JuliusBrussee/caveman) | Ultra-compressed response style (`lite`/`full`/`ultra`), cutting roughly 65% of output tokens without losing technical substance. Includes `caveman-commit` and `caveman-review`. |

## MCP servers

> MCP (Model Context Protocol) servers extend Claude Code with access to external services and tools.

| MCP server | Description |
|------------|-------------|
| [`chrome-devtools`](https://claude.com/plugins/chrome-devtools-mcp) | Browser control: screenshots, clicks, navigation, DevTools, Lighthouse audits, performance traces |
| [`context7`](https://claude.com/plugins/context7) | Up-to-date library and framework documentation delivered straight into the LLM context |
| [`exa`](https://exa.ai/docs/reference/exa-mcp#claude-code) | Semantic web search and content extraction |
| [`serper`](https://github.com/marcopesani/mcp-server-serper?tab=readme-ov-file#installing-via-smithery) | Google Search API — web search and page scraping |
| [`tavily`](https://docs.tavily.com/documentation/mcp#connect-to-claude-code) | Research-oriented search: crawl, extract, map, research |
| [`figma`](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/#claude-code) | Figma integration for working with design files |

## Plugins

> A Claude Code plugin is an installable module that can bundle skills, hooks, subagents and MCP servers together.

| Plugin | Description |
|--------|-------------|
| [superpowers](https://claude.com/plugins/superpowers) | Agent skill framework and development methodology: brainstorming, planning, TDD, debugging, code review, git worktrees and more. |
| [code-simplifier](https://claude.com/plugins/code-simplifier) | Agent that simplifies and refactors code while preserving behaviour |
| [claude-md-management](https://claude.com/plugins/claude-md-management) | Tooling for maintaining and improving CLAUDE.md files |
| [pr-review-toolkit](https://claude.com/plugins/pr-review-toolkit) | Comprehensive PR review through specialised agents |
| [claude-code-setup](https://claude.com/plugins/claude-code-setup) | Analyses a codebase and recommends a Claude Code configuration for it |
| [explanatory-output-style](https://claude.com/plugins/explanatory-output-style) | Educational insights into implementation choices and code patterns |
| [skill-creator](https://claude.com/plugins/skill-creator) | Creating, improving and testing skills |
| [typescript-lsp](https://claude.com/plugins/typescript-lsp) | TypeScript Language Server Protocol — types, autocomplete, diagnostics |
| [frontend-design](https://claude.com/plugins/frontend-design) | Skill for building high-quality UI |

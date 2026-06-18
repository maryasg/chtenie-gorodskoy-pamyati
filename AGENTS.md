# AGENTS.md

## Cursor Cloud specific instructions

This is a **Vite + React 19 + TypeScript + Tailwind v4** single-page app (no backend, no database). It is a static frontend; there are no services other than the Vite dev server.

### Running / building / testing
- Dev server: `npm run dev` (Vite, serves on port `5173`). Standard commands live in `package.json` and `README.md`.
- Lint: `npm run lint` (ESLint flat config in `eslint.config.js`).
- Build: `npm run build` (`tsc -b` then `vite build`, output in `dist/`). There is no test runner configured.

### Non-obvious gotchas
- The app is served under a **base path**: `base: "/chtenie-gorodskoy-pamyati/"` in `vite.config.ts`. The dev server root URL is `http://localhost:5173/chtenie-gorodskoy-pamyati/` — the bare `http://localhost:5173/` returns 404. The React Router `basename` is derived from `import.meta.env.BASE_URL`.
- `vite build` also copies `dist/index.html` to `dist/404.html` (GitHub Pages SPA fallback) via a custom plugin in `vite.config.ts`.
- Deploy is via GitHub Actions (`.github/workflows/deploy-pages.yml`, preview workflows); no manual deploy step needed locally.

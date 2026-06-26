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

### Archiview CV (`tools/archiview-cv/`)
- Maria runs **v16** from Desktop (`archiview_cv_easy_v16_package`), synced via `setup_v16_desktop.bat` — not directly from git.
- **Python 3.10–3.13 only**; 3.14 breaks NumPy/OpenCV (`install_windows.bat` rejects it).
- **All `.ps1` string literals must be ASCII** — see `tools/archiview-cv/ENCODING_RULES.md`. Run `check_ps1_encoding.bat` before committing script changes.
- Site facade: `ArchiviewFacadePanel` uses `marked-facade.png` (06) with hover-only curator plaques; multi-comparison via `public/explorer/*/manifest.json`.
- Full agent context: `tools/archiview-cv/TECHNICAL_NOTES_RU.md` and repo root `ПРОДОЛЖИТЬ_РАБОТУ.md`.

### Unrelated projects (do not mix with this repo)

- **Dental clinic article generator** lives in a separate repository: `maryasg/maryasg-articles_KorolevSP` on the user's PC at `maryasg-articles_KorolevSP`. It was briefly added as `ksp-content-generator/` here and removed — do not restore it into this site repo.

### Archiview CV (`tools/archiview-cv/`) — Windows + Cyrillic

Maria uses **cmd on Windows**; Desktop paths include Cyrillic (`Проект Память стен`).

**Read `tools/archiview-cv/ENCODING_RULES.md` before editing scripts.**

Summary:
- **`.ps1`**: ASCII-only string literals (no Cyrillic, no `—`, no `…`). Parser errors otherwise.
- **`.bat`**: Russian `echo` is OK; use `chcp 65001`; call `.ps1` for file copies to Cyrillic paths.
- **Never** use `robocopy`/`copy` in `.bat` for Desktop sync — use existing `*_desktop.ps1` via `.bat` wrappers.
- User runs `setup_v16_desktop.bat` from cmd; launches `ZAPUSK_V16.bat` from Desktop `archiview_cv_easy_v16_package`.

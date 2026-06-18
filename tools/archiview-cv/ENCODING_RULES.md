# Encoding rules for Archiview scripts (agents)

Maria runs Archiview on **Windows in Russian locale** (cmd, not PowerShell UI).
Desktop paths contain **Cyrillic**, e.g. `Desktop\Cult Tech\Проект Память стен\...`.

## PowerShell (`.ps1`) — ASCII only in source code

**Never put Cyrillic or Unicode punctuation inside `.ps1` string literals.**

Windows PowerShell 5.1 reads `.ps1` as the system code page (often CP1251).
UTF-8 without BOM or smart punctuation breaks the parser:

```
The string is missing the terminator: '.
```

### Forbidden in `.ps1`

| Do not use | Use instead |
|------------|-------------|
| Cyrillic in `'...'` or `"..."` | English in `.ps1`; Russian in `.bat` or `README_*_ru.md` |
| Em dash `—` (U+2014) | ASCII hyphen `-` |
| Ellipsis `…` (U+2026) | Three dots `...` |
| Curly quotes `“` `”` | Straight quotes `'` `"` |

### Allowed in `.ps1`

- English `Write-Host` messages
- Paths from variables (`$V16Root`, `Join-Path`, `-LiteralPath`) — Cyrillic **paths on disk** are fine
- `Copy-Item -LiteralPath` for Desktop folders with Russian names

### If Russian UI text is needed

Put it in **`.bat`** files (`echo ...`) with `chcp 65001` at the top, or in **`README_v16_ru.md`**.

`.bat` callers may invoke `.ps1` internally; the user only double-clicks `.bat`.

## cmd (`.bat`) — Cyrillic OK with UTF-8 code page

At the start of user-facing `.bat`:

```bat
@echo off
chcp 65001 >nul 2>&1
```

Do **not** use `robocopy` / `copy` to paths with Cyrillic — delegate to `.ps1` with `Copy-Item -LiteralPath`.

## File copy to Desktop

| Task | Tool |
|------|------|
| Bootstrap v15 → v16 | `bootstrap_v16_desktop.ps1` (from `.bat`) |
| Sync repo → Desktop | `sync_to_v16_desktop.ps1` (from `.bat`) |
| User entry point | `setup_v16_desktop.bat` only |

## Check before commit

From repo root:

```bash
python3 -c "
from pathlib import Path
for p in Path('tools/archiview-cv').glob('*.ps1'):
    bad = [i for i,l in enumerate(p.read_bytes().splitlines(),1) if any(b>127 for b in l)]
    if bad: print(p, 'non-ASCII lines:', bad)
"
```

Must print nothing for `.ps1` files.

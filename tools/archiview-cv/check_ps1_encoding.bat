@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo Checking .ps1 files for non-ASCII characters...
echo.

python -c "from pathlib import Path; bad=False
for p in sorted(Path('.').glob('*.ps1')):
    lines=[i+1 for i,l in enumerate(p.read_bytes().splitlines()) if any(b>127 for b in l)]
    if lines:
        bad=True
        print('FAIL:', p.name, 'lines', lines)
if not bad:
    print('OK: all .ps1 files are ASCII-only')
    exit(0)
exit(1)" 2>nul
if errorlevel 1 (
    py -3 -c "from pathlib import Path; bad=False
for p in sorted(Path('.').glob('*.ps1')):
    lines=[i+1 for i,l in enumerate(p.read_bytes().splitlines()) if any(b>127 for b in l)]
    if lines:
        bad=True
        print('FAIL:', p.name, 'lines', lines)
if not bad:
    print('OK: all .ps1 files are ASCII-only')
    exit(0)
exit(1)"
)
set ERR=%ERRORLEVEL%
echo.
if %ERR% neq 0 (
    echo See ENCODING_RULES.md - use English in .ps1 string literals.
    pause
    exit /b 1
)
pause
exit /b 0

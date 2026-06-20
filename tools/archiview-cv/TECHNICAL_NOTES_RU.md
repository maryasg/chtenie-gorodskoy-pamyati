# Archiview + сайт — технические заметки (для агентов и разработчиков)

Обновлено: **2026-06-20**. Дополняет `README_v16_ru.md` (Maria) и `ПРОДОЛЖИТЬ_РАБОТУ.md` (handoff в новый чат).

---

## Окружение Maria (Windows)

| Параметр | Значение |
|----------|----------|
| Репозиторий | `C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati` |
| Archiview v16 (рабочая) | `Desktop\...\archiview_cv_easy_v16_package` |
| Archiview v15 (запасная) | `archiview_cv_easy_v15_package` — не ломать |
| Shell | **cmd** + `.bat`; PowerShell только внутри скриптов |
| Путь Desktop | Часто **кириллица** (`Проект Память стен`) и **`!`** в `Cult Tech` |
| Git push | GitHub Desktop (терминал иногда без auth) |

После **любых** правок в `tools/archiview-cv/` из git:

```bat
cd tools\archiview-cv
setup_v16_desktop.bat
```

Иначе на Desktop остаётся старый `copy_to_website.ps1` / `archiview_gui.py`.

---

## Python

| Версия | Статус |
|--------|--------|
| **3.10 – 3.13** | OK (`install_windows.bat` ищет 3.12 → 3.11 → 3.13 → 3.10) |
| **3.14+** | **Нельзя** — NumPy/OpenCV падают при импорте |

Если venv сломан: `PERESOZDAT_VENV.bat` → `install_windows.bat` → `ZAPUSK_V16.bat`.

В коде Archiview: `ARCHIVIEW_APP_VERSION=16` (по умолчанию) → класс `AppV16`.

---

## Кодировки и PowerShell

**Обязательно:** `ENCODING_RULES.md`

Кратко:

- В **`.ps1` только ASCII** в строковых литералах (никакой кириллицы, `—`, `…`, `→` в исходнике `.ps1`).
- Кириллица в **`.bat`** с `chcp 65001` — OK.
- Копирование на Desktop с русскими путями — через **PowerShell `Copy-Item -LiteralPath`**, не `robocopy` из bat.

Проверка перед коммитом:

```bat
cd tools\archiview-cv
check_ps1_encoding.bat
```

Типичные поломки `copy_to_website.ps1`: слова `сегодня`, `Primary (active)` с кириллицей, em dash `—` → `ParserError: UnexpectedToken`.

---

## Картинки: что где (overlay)

| Файл в папке cmp | Назначение |
|------------------|------------|
| `03_historical_rectified.png` | Выпрямленное историческое |
| `04_modern_rectified.png` | Выпрямленное современное |
| `05_comparison_for_labeling.png` | **Фон разметки** (overlay / до-после / настройки с вкладки «3. Сравнение») |
| `06_marked_rectified.png` | Обводки на **выпрямленном** modern → на сайт как `marked-facade.png` |
| `07_marked_on_original_modern.png` | Архив на полном кадре; **не** основа интерактива на сайте |
| `08_marked_on_original_modern_labeled.png` | С подписями на фото; не для hover-плашек на сайте |
| `10_side_by_side_marked.png` | Режим разных ракурсов |

### Archiview UI

| Вкладка | Фон |
|---------|-----|
| 3. Сравнение | Живой preview (ползунки) |
| 4. Разметка | `05` (синхронизируется с вкладкой 3 автоматически + кнопка «Применить к разметке») |
| 5. Результат | **04** modern rectified + номера областей (не overlay 05) |

### Сайт (`ArchiviewFacadePanel.tsx`)

| Элемент | Поведение |
|---------|-----------|
| Фон | `modern-rectified.png` (= **04**) — как вкладка «Результат»; подсветка при наведении (SVG) |
| Запасной файл | `marked-facade.png` (= 06) — экспорт для архива; на сайте не обязателен для overlay |
| Кураторские плашки | **Только при наведении** на область |
| Координаты SVG | `buildRegionsRectified` — **без** гомографии H |
| Несколько сравнений | `public/explorer/MOSCOW_NNN/manifest.json` + `ArchiviewComparisonPicker` |

---

## Несколько сравнений на дом

Структура проекта:

```
comparisons/
  index.json          # active_comparison_id, список cmp, has_markup, historical_year, modern_year
  cmp_005/            # рабочая папка
  cmp_008/
result/               # legacy mirror → cmp_legacy_001
```

Экспорт (`copy_to_website.ps1`):

- **★ active** → файлы в корень `public/explorer/MOSCOW_NNN/`
- Остальные cmp → `public/explorer/MOSCOW_NNN/comparisons/cmp_XXX/`
- **`cmp_legacy_001` не экспортируется** (status discarded или `is_legacy`)
- `manifest.json` с годами (`historicalPhotoYear`, `modernPhotoYear`)

MOSCOW_001 (эталон):

| cmp | Годы |
|-----|------|
| cmp_005 ★ | 1924 → 2026 |
| cmp_008 | 1840 → 2026 |

---

## Git: конфликт `manifest.json`

При `git pull` часто конфликт **только в `updatedAt`** (Maria экспортировала на сайт локально, в git — другая метка времени).

Решение:

```bat
git checkout --theirs public\explorer\MOSCOW_001\manifest.json
git add public\explorer\MOSCOW_001\manifest.json
git commit -m "resolve manifest conflict"
```

Или вручную удалить маркеры `<<<<<<<` / `=======` / `>>>>>>>`, оставить один блок `comparisons` без legacy.

**Перед экспортом:** `git pull origin main` — меньше конфликтов.

---

## Ключевые файлы (2026-06)

```
tools/archiview-cv/
  archiview_gui.py              # UI v16, сравнение→разметка, localhost
  archiview_project_model.py    # cmp, has_markup, years, legacy
  archiview_project_ui.py       # таблица сравнений, годы
  copy_to_website.ps1           # экспорт + manifest (ASCII only!)
  ENCODING_RULES.md
  TECHNICAL_NOTES_RU.md         # этот файл
  setup_v16_desktop.bat / sync_to_v16_desktop.ps1

src/
  components/ArchiviewFacadePanel.tsx
  components/ArchiviewComparisonPicker.tsx
  data/explorer/explorerManifest.ts
  pages/BuildingPage.tsx

public/explorer/MOSCOW_001/manifest.json
```

---

## Чеклист агента перед PR

1. `check_ps1_encoding.bat` — нет non-ASCII в `.ps1`
2. `python3 -m py_compile tools/archiview-cv/archiview_gui.py` …
3. Не менять поведение v15 Desktop без необходимости
4. Документировать в `ПРОДОЛЖИТЬ_РАБОТУ.md` если меняется workflow Maria
5. После правок `.ps1` — напомнить про `setup_v16_desktop.bat`

---

## История изменений (июнь 2026)

| PR / тема | Суть |
|-----------|------|
| v16 wizard | Вкладка «0. Дом и сравнение», rakurs overlay / side_by_side |
| localhost | «Показать на сайте» + fix кириллицы в ps1 |
| multi-comparison | manifest.json, переключатель по годам на сайте |
| legacy / years | Скрытие legacy с сайта, `has_markup`, годы вместо cmp_XXX |
| facade panel | Сайт: 06 с подсветкой, плашки при hover |
| compare→markup | Автосохранение 05 при смене overlay на вкладке 3 |
| corner picker | zoom/pan в окне углов |
| photo lock | Нельзя менять фото если есть разметка/выпрямление |

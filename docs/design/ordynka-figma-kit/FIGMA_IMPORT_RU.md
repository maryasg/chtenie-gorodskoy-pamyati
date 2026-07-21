# Карточка Ордынки — набор для Figma

Готовый **макетный комплект** для карточки `MOSCOW_001_kumaninykh` (стиль Arki / v2): имена слоёв A–E, токены, картинки фасада и PNG-референсы с сайта.

> **Почему не один файл `.fig`?**  
> В облачном агенте нет подключения к вашему аккаунту Figma (нужен Figma Desktop + авторизация MCP). Этот набор можно за **10–15 минут** собрать в Figma вручную по инструкции ниже — слои уже названы так же, как в коде и в переписке.

**Живая страница (превью PR):**  
https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-152/v2/building/MOSCOW_001_kumaninykh/

**Код страницы:** `src/v2/pages/building/OrdynkaArkiPage.tsx`  
**Стили:** `src/v2/arki-theme.css`  
**Токены:** [`design-tokens.json`](./design-tokens.json)  
**Дерево слоёв (машиночитаемое):** [`layer-tree.json`](./layer-tree.json)

---

## Словарь блоков (как просить правки)

| Код | Имя в Figma | Что это |
|-----|-------------|---------|
| CHROME | вне фрейма CARD | Шапка сайта v2 (`LayoutV2`), не часть карточки |
| **A** | `A · CARD-HEADER` | Шапка карточки: бейдж, название, карта, датировка |
| A1 | `A1 · badge + Object ID` | Verified + `MOSCOW_001 · 77-04-A017` |
| A2 | `A2 · title + geo` | Заголовок и адрес |
| A3 | `A3 · map link + dating` | Ссылка на карту и список дат |
| **B** | `B · HERO-GRID` | Три колонки: легенда · чертёж · инспектор |
| B1 | `B1 · legend` | Legend · фрагмент 01A |
| B2 | `B2 · labeled facade` | Картинка `marked-facade-labeled.png` |
| B3a | `B3a · layer checklist` | Чекбоксы слоёв 1840…2026 |
| B3b | `B3b · crossfade` | Виджет 1840→2026 |
| **C** | `C · FACADE-READING` | Чтение фасада + группы L/K/A |
| C1c | `C1c · facade panel` | Интерактивная панель Archiview |
| C2 | `C2 · overlay groups` | L·01, K·02, A·03 |
| **D** | `D · NARRATIVE` | Текст «Чтение фасада» + 4 счётчика |
| **E** | `E · DOSSIER` | Таблица слоёв, артефакты, источники, футер |

---

## Быстрый старт в Figma (Desktop)

### 1. Новый файл

1. Figma → **New design file** → имя: `Ordynka · MOSCOW_001 v2`.
2. Frame **1440×Auto**, имя: `ORDYNKA / MOSCOW_001 / Desktop 1440`, заливка `#F7F7F5`.

### 2. Референс (заблокировать)

1. Перетащите в фрейм файл  
   `docs/design/ordynka-figma-kit/assets/reference/00-full-page-1440.png`  
   (если папки `reference` ещё нет — выполните `node docs/design/ordynka-figma-kit/capture-screenshots.mjs`).
2. Слой назовите `_REFERENCE / full page` → **Lock**.

### 3. Структура слоёв поверх референса

Создайте **пустые фреймы** (auto-layout по вертикали, gap 32) с точными именами:

```
ORDYNKA / MOSCOW_001 / Desktop 1440
├── _REFERENCE / full page          (locked)
├── A · CARD-HEADER
├── B · HERO-GRID
│   ├── B1 · legend
│   ├── B2 · labeled facade       ← вставить PNG из assets/cmp_005/
│   └── B3 · inspector
│       ├── B3a · layer checklist
│       └── B3b · crossfade
├── C · FACADE-READING
│   ├── C1 · main column
│   └── C2 · overlay groups
├── D · NARRATIVE
└── E · DOSSIER
```

Имена можно копировать из [`layer-tree.json`](./layer-tree.json).

### 4. Шрифты и цвета

Установите в Figma (Google Fonts):

- **Cormorant Garamond** — заголовки (блоки A2, C1a, D1).
- **IBM Plex Mono** — всё остальное UI.

Создайте **Color styles** из [`design-tokens.json`](./design-tokens.json): `ink`, `muted`, `red`, `bg`.

Обводки сетки: **1 px**, цвет `ink`.

### 5. Картинки фасада

Из папки [`assets/`](./assets/) перетащите в соответствующие фреймы:

- B2 → `cmp_005/marked-facade-labeled.png`
- C1c → `cmp_005/marked-facade.png` (как нижний слой; сверху — плейсхолдеры регионов при необходимости)
- Для вариантов сравнения — `cmp_008/`, `cmp_009/`

Список файлов: [`assets/README.md`](./assets/README.md).

### 6. Рабочий режим

1. Скрыть `_REFERENCE` когда верстаете сами.
2. Правки обсуждаем по кодам: «сделай B2 выше», «C2 — другой отступ».
3. После согласования макета — те же коды в задаче для кода на сайте.

---

## Создать Figma-файл через Cursor на вашем ПК

Если у вас в **Cursor Desktop** подключён Figma MCP:

1. Откройте этот репозиторий локально.
2. Попросите агента: «Создай Figma-файл из `docs/design/ordynka-figma-kit`» — он сможет вызвать `create_new_file` + `generate_figma_design` с URL превью выше.

---

## Обновление PNG с сайта

```bash
# Локально
npm run dev
node docs/design/ordynka-figma-kit/capture-screenshots.mjs

# Или с GitHub Pages
ORDYNKA_SCREENSHOT_URL="https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-152/v2/building/MOSCOW_001_kumaninykh/" \
  node docs/design/ordynka-figma-kit/capture-screenshots.mjs
```

Скрипт требует пакет `playwright` (один раз: `npx playwright install chromium`).

---

## Связанные материалы

- Превью v2: `/v2/building/MOSCOW_001_kumaninykh/`
- Референс Lovable: https://arki-view-magic.lovable.app/building/05
- PR с вёрсткой: https://github.com/maryasg/chtenie-gorodskoy-pamyati/pull/152

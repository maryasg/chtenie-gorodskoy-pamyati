# Blueprint · design-файл Figma для всего сайта

Чеклист страниц и фреймов, чтобы в Figma была **полная картина** (не только Ордынка).

Используйте вместе с [DEVELOPER_MAP_RU.md](../DEVELOPER_MAP_RU.md).

---

## Имя файла

`Память стен · продукт + v2` (или один файл на команду в Drafts).

---

## Страницы (Pages) в Figma

### 00 · Карта сайта

Один фрейм **1920×1080**, блок-схема:

- Колонка **v1** — все URL из `App.tsx` (Layout).
- Колонка **v2** — `/v2/*` (LayoutV2).
- Под каждым URL — **подпись файла** `src/pages/...` или `src/v2/...`.
- Стрелка **данные**: `src/data/buildings`, `public/explorer/`.

*Скрипт:* `figma-scripts/05-site-pages-map.js` (добавляет эту страницу).

### 01 · Схема проекта

Скрипт `02-project-scheme.js` — роутинг, Ordynka vs default.

### 02 · Design tokens

Скрипт `03-design-tokens.js` + при росте v2 добавить переменные из `theme.css`.

### 03 · Компоненты (library)

Фреймы-спеки (не обязательно component set на старте):

| Имя в Figma | Код |
|-------------|-----|
| `CMP / ArchiviewFacadePanel` | `ArchiviewFacadePanel.tsx` |
| `CMP / FacadeTimeLayers` | `FacadeTimeLayers.tsx` |
| `CMP / V2Plate` | `V2Plate.tsx` |
| `CMP / MapView` | `MapView.tsx` |
| `CMP / TransformationTimeline` | `TransformationTimeline.tsx` |

### 04 · v1 · Экраны

По одному фрейму **1440** (или 390 mobile):

| Фрейм | URL |
|-------|-----|
| `v1 / Map` | `/` |
| `v1 / Building` | `/building/MOSCOW_001_kumaninykh` |
| `v1 / Method` | `/method` |
| `v1 / Tour` | `/tour` |
| `v1 / Explorer` | `/explorer` |
| `v1 / Expert` | `/expert/...` |

Референс: прод https://maryasg.github.io/chtenie-gorodskoy-pamyati/

### 05 · v2 · Экраны

| Фрейм | URL |
|-------|-----|
| `v2 / Home` | `/v2/` |
| `v2 / Map` | `/v2/map` |
| `v2 / Building default` | `/v2/building/MOSCOW_002_...` (не Ordynka) |

Превью PR: `.../pr-preview/pr-152/v2/`

### 06 · Ordynka · CARD A–E

Скрипт `04-card-layers.js` — детальная иерархия.

### 07 · Референс / captures

`generate_figma_design` с URL превью или PNG из `ordynka-figma-kit/assets/reference/`.

---

## Именование слоёв (правило)

```
{версия} / {экран} / {блок} / {элемент}
```

Примеры:

- `v2 / Ordynka / B · HERO-GRID / B2 · facade image`
- `v1 / Building / timeline / row-03`

Совпадает с `data-figma-block` на Ordynka в коде.

---

## Порядок сборки через MCP (Desktop)

1. `whoami` → `create_new_file`
2. `01-create-pages.js` (обновлён: включает страницу 00)
3. `05-site-pages-map.js`
4. `02` → `03` → `04`
5. `generate_figma_design` для нужных URL на страницу 07

Промпт-шаблон: [ordynka-figma-kit/ЗАПУСК_В_FIGMA.md](./ordynka-figma-kit/ЗАПУСК_В_FIGMA.md) — допишите шаг 5.

---

## Что не переносить в Figma

- Логика `explorerManifest.ts`, `resolveDefaultComparisonId`
- Геометрия регионов в `annotations.json`
- Скрипты `tools/archiview-cv/`

В Figma достаточно **подписи**: «данные: public/explorer/MOSCOW_001/manifest.json».

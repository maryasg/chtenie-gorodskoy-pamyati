# Ассеты для макета Figma · MOSCOW_001 (Ордынка)

Пути относительно этой папки.

## Сравнения фасада (Archiview)

| Файл | Где в макете |
|------|----------------|
| `cmp_005/marked-facade-labeled.png` | **B2** — герой, размеченный чертёж |
| `cmp_005/marked-facade.png` | **C1c** — панель с номерами регионов |
| `cmp_005/historical-rectified.png` | слой подложки (история) |
| `cmp_005/modern-rectified.png` | слой подложки (современность) |
| `cmp_008/marked-facade-labeled.png` | вариант сравнения 1938→2026 |
| `cmp_009/marked-facade-labeled.png` | вариант сравнения 1840→2026 |

`modern-source.png` для cmp_005 в превью может отсутствовать — на сайте подставляется запасной кадр из кода.

## Кроссфейд (блок B3b)

| Файл | Год |
|------|-----|
| `time-layers/1840.jpg` | 1840 |
| `time-layers/1924.jpg` | 1924 |
| `time-layers/1930.jpg` | 1930–1936 |
| `time-layers/2026.jpg` | 2026 |

## Референс со страницы

Папка `reference/` — PNG с живой карточки (скрипт `capture-screenshots.mjs`):

- `00-full-page-1440.png` — вся страница
- `A-CARD-HEADER.png` … `E-DOSSIER.png` — по блокам A–E

Обновить снимки после правок вёрстки:

```bash
npm run dev
node docs/design/ordynka-figma-kit/capture-screenshots.mjs
```

Превью на GitHub Pages (без локального сервера):

```bash
ORDYNKA_SCREENSHOT_URL="https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-152/v2/building/MOSCOW_001_kumaninykh/" \
  node docs/design/ordynka-figma-kit/capture-screenshots.mjs
```

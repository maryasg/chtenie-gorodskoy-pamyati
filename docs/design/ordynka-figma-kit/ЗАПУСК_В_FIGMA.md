# Запуск: схема проекта + слои карточки в Figma

**Важно:** облачный агент **не видит** ваш Figma MCP. Эти шаги выполняются в **Cursor на вашем ПК**, где Figma уже подключена.

## Один промпт для Agent (скопируйте целиком)

```text
Figma MCP подключён. Создай design-файл для проекта «Память стен»:

1. whoami — возьми planKey.
2. create_new_file: fileName «Память стен · схема + Ordynka карточка», editorType design.
3. use_figma (fileKey из шага 2, skillNames figma-use,figma-generate-design) — выполни по очереди содержимое файлов из репозитория:
   - docs/design/ordynka-figma-kit/figma-scripts/01-create-pages.js
   - docs/design/ordynka-figma-kit/figma-scripts/05-site-pages-map.js
   - docs/design/ordynka-figma-kit/figma-scripts/02-project-scheme.js
   - docs/design/ordynka-figma-kit/figma-scripts/03-design-tokens.js
   - docs/design/ordynka-figma-kit/figma-scripts/04-card-layers.js
4. generate_figma_design в тот же fileKey: захвати полную страницу превью на страницу «04 · Референс»:
   https://maryasg.github.io/chtenie-gorodskoy-pamyati/pr-preview/pr-152/v2/building/MOSCOW_001_kumaninykh/
5. Верни file_url открытого файла и кратко опиши 4 страницы.
```

Откройте репозиторий локально (ветка `cursor/lovable-design-v2-3b69` или `main` после merge).

## Что появится в Figma (4 страницы)

| Страница | Содержание |
|----------|------------|
| **00 · Карта сайта** | Все URL v1/v2 и пути к файлам в `src/` |
| **01 · Схема проекта** | GitHub Pages, v1/v2, маршруты, Ordynka vs остальные здания, чипы A–E |
| **02 · Design tokens** | Цвета Arki, шрифты, ссылка на `arki-theme.css` |
| **03 · Карточка · слои** | Фрейм 1440 с вложенными **A–E** и подслоями (A1, B2, C1c…) |
| **04 · Референс** | Скрин живой карточки с превью (шаг 4) |

## Дополнительно вручную

- Картинки фасада: `docs/design/ordynka-figma-kit/assets/` → в слой **B2** на странице 03.
- Блоковые PNG: `assets/reference/A-CARD-HEADER.png` … `E-DOSSIER.png`.

## FigJam (опционально)

Для блок-схемы только архитектуры можно отдельно вызвать `generate_diagram` с файлом  
`docs/design/ordynka-figma-kit/project-scheme-flowchart.mmd`.

## Если что-то падает

- **Шрифты:** скрипты используют IBM Plex Mono / Cormorant; при отсутствии — Inter.
- **Ошибка в 03-design-tokens:** проверьте синтаксис в скрипте (агент читает файл с диска).
- **Пустой референс:** откройте URL превью в браузере; при 404 обновите номер PR в URL.

После создания пришлите **file_url** — можно доработать слои по вашим правкам (тоже через локальный Agent).

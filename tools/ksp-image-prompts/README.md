# Промпты для обложек статей (KSP)

Скрипты и **полная инструкция** для репозитория **maryasg-articles_KorolevSP**.

- **[ЗАПУСК_ПАНЕЛИ.bat](ЗАПУСК_ПАНЕЛИ.bat)** — окно с кнопками: темы → API → статьи → промпты → Word
- **[ПАНЕЛЬ_РАБОТЫ.html](ПАНЕЛЬ_РАБОТЫ.html)** — кликабельная подсказка «куда нажимать»
- **[ИНСТРУКЦИЯ_ДЛЯ_ПЕЧАТИ.md](ИНСТРУКЦИЯ_ДЛЯ_ПЕЧАТИ.md)** — короткая пошаговая версия для печати
- **[ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md)** — полная инструкция: новые темы, генерация статей, обложки ChatGPT
- Скрипты и инструкции ниже — копируются в папку статей через `СКОПИРОВАТЬ_В_СТАТЬИ.bat` (включая панель, `generate.py`, `docx_export.py`, `export_docx.bat`, `pack_month.bat`)

## Быстрый старт (Windows)

**Панель с кнопками (рекомендуется):**

```bat
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\ksp-image-prompts
СКОПИРОВАТЬ_В_СТАТЬИ.bat
cd C:\Users\Marusia\Projects\maryasg-articles_KorolevSP
ЗАПУСК_ПАНЕЛИ.bat
```

**Плоские файлы за месяц (ВК + Telegram + картинки):**

```bat
cd C:\Users\Marusia\Projects\maryasg-articles_KorolevSP
СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat июнь
```

Или из репозитория сайта:

```bat
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\ksp-image-prompts
СОБРАТЬ_ПЛОСКИЕ_ФАЙЛЫ.bat июнь
```

1. Обновите **сайт** из GitHub (`git pull` в `chtenie-gorodskoy-pamyati`).
2. Запустите из cmd:

```bat
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\ksp-image-prompts
СКОПИРОВАТЬ_В_СТАТЬИ.bat
```

3. Промпты появятся в `C:\Users\Marusia\Projects\maryasg-articles_KorolevSP\image_prompts\`.

## Вручную

Скопируйте в корень `maryasg-articles_KorolevSP`:

- `build_image_prompts.py`
- `build_image_prompts.bat`
- `prompts/cover_template_title.txt`

Затем:

```bat
cd C:\Users\Marusia\Projects\maryasg-articles_KorolevSP
build_image_prompts.bat
```

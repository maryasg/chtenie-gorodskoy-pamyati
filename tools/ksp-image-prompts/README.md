# Промпты для обложек статей (KSP)

Скрипты для репозитория **maryasg-articles_KorolevSP** — пока их нет в GitHub статей, они лежат здесь.

## Быстрый старт (Windows)

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

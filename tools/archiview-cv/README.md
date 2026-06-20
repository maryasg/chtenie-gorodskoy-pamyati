# Archiview CV (в репозитории сайта)

Рабочая программа Maria — **отдельная папка v16 на рабочем столе** (`archiview_cv_easy_v16_package`).

Здесь в Git — код, чтобы не потерять версию вместе с сайтом.

## Документация

| Файл | Для кого |
|------|----------|
| [README_v16_ru.md](README_v16_ru.md) | Maria — установка, вкладки, localhost |
| [README_v15_ru.md](README_v15_ru.md) | Старая v15 (запасная) |
| [ENCODING_RULES.md](ENCODING_RULES.md) | Агенты — **только ASCII в .ps1** |
| [TECHNICAL_NOTES_RU.md](TECHNICAL_NOTES_RU.md) | Агенты — Python, картинки, manifest, git |
| [КАК_РАБОТАЕТ_ПАПКА_ПРОЕКТА_ru.md](КАК_РАБОТАЕТ_ПАПКА_ПРОЕКТА_ru.md) | Структура папки дома |
| [../../ПРОДОЛЖИТЬ_РАБОТУ.md](../../ПРОДОЛЖИТЬ_РАБОТУ.md) | Handoff для нового чата Cursor |

## Быстрый старт (Maria)

```bat
cd tools\archiview-cv
setup_v16_desktop.bat
```

На Desktop в папке v16: `install_windows.bat` (первый раз), затем `ZAPUSK_V16.bat`.

## Результат → сайт

1. Archiview: «Отправить на сайт» или `copy_to_website.bat`
2. GitHub Desktop: Commit + Push
3. Ctrl+F5 на странице дома

Проверка `.ps1` перед коммитом: `check_ps1_encoding.bat`

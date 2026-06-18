# Archiview CV v15 (копия в репозитории сайта)

**Сейчас по умолчанию запускается v15** (v16 отложена).

Актуальная папка на рабочем столе:
`archiview_cv_easy_v15_package` (или v16 — синхронизация обновит файлы внутри).

## Быстрый старт

`install_windows.bat` → `run_gui_windows.bat`. В заголовке окна: **v15**.

## Синхронизация Desktop ← git

```powershell
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\archiview-cv
powershell -ExecutionPolicy Bypass -File .\sync_to_v15_desktop.ps1
```

## Если разметка пропала (дом со зверями)

```powershell
powershell -ExecutionPolicy Bypass -File .\restore_markup_from_website.ps1 -CardId MOSCOW_003
```

## На сайт

«На сайт» или `copy_to_website.bat` → GitHub Desktop → Push.

Подробно: `README_v15_ru.md` на Desktop.

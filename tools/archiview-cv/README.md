# Archiview CV

Две папки на рабочем столе:

| Папка | Версия | Зачем |
|--------|--------|--------|
| `archiview_cv_easy_v15_package` | v15 | Стабильная, без редактирования точек |
| `archiview_cv_easy_v16_package` | v16 | Редактирование вершин полигонов |

## v15 (как сейчас)

```powershell
powershell -ExecutionPolicy Bypass -File .\sync_to_v15_desktop.ps1
```

Запуск: `run_gui_windows.bat` в папке v15. Заголовок: **v15**.

## v16 (редактирование областей)

Первый раз:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap_v16_desktop.ps1
powershell -ExecutionPolicy Bypass -File .\sync_to_v16_desktop.ps1
```

В папке v16: `install_windows.bat` → `run_gui_windows.bat`. Заголовок: **v16 polygon edit**.

Подробно: `README_v16_ru.md`.

## Если разметка пропала

```powershell
powershell -ExecutionPolicy Bypass -File .\restore_markup_from_website.ps1 -CardId MOSCOW_003
```

## На сайт

`copy_to_website.bat` → GitHub Desktop → Push.

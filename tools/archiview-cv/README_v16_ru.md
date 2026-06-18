# Archiview CV v16

**Отдельная папка на рабочем столе:** `archiview_cv_easy_v16_package`  
**Старая стабильная v15** остаётся в `archiview_cv_easy_v15_package` — не трогаем.

## Первый раз: создать папку v16

```powershell
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\archiview-cv
powershell -ExecutionPolicy Bypass -File .\bootstrap_v16_desktop.ps1
powershell -ExecutionPolicy Bypass -File .\sync_to_v16_desktop.ps1
```

В папке v16 на рабочем столе:

```bat
install_windows.bat
run_gui_windows.bat
```

В заголовке окна: **v16 polygon edit + stable site links**.

## Обновление после git pull

```powershell
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\archiview-cv
powershell -ExecutionPolicy Bypass -File .\sync_to_v16_desktop.ps1
```

v15 обновляется отдельно: `sync_to_v15_desktop.ps1` — в папку v15.

## Редактирование областей (новое в v16)

1. Вкладка **4. Разметка**
2. В списке **«Области»** выберите номер
3. **«Редактировать точки выбранной области»**
4. Тяните жёлтые точки мышью
5. Клик **по линии** — новая точка
6. **Delete** — убрать выбранную точку (минимум 3)
7. **«Завершить редактирование»** — выйти из режима
8. **Сохранить разметку** — как раньше

Номера областей (`id`) и связи `traceId` на сайте при правке **не сбрасываются**.

В режиме «два окна» (разные ракурсы) редактирование точек пока недоступно — только overlay (одно окно).

## На сайт

«На сайт» или `copy_to_website.bat` → GitHub Desktop → Push.

## Если разметка пропала

```powershell
powershell -ExecutionPolicy Bypass -File .\restore_markup_from_website.ps1 -CardId MOSCOW_003
```

(укажите свой CardId)

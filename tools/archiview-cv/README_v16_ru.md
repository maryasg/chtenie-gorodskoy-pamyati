# Archiview CV v16

**Отдельная папка на рабочем столе:** `archiview_cv_easy_v16_package`  
**Старая стабильная v15** остаётся в `archiview_cv_easy_v15_package` — не трогаем.

## Первый раз: создать папку v16

```powershell
cd C:\Users\Marusia\Projects\chtenie-gorodskoy-pamyati\tools\archiview-cv
git pull
powershell -ExecutionPolicy Bypass -File .\setup_v16_desktop.ps1
```

Откроется папка v16. В ней:

```bat
install_windows.bat
ZAPUSK_V16.bat
```

В заголовке окна: **v16 polygon edit**. Зелёная строка: **★ Archiview CV v16 ★**.  
Если **v15** — вы в папке `archiview_cv_easy_v15_package` (не та).

## Обновление после git pull

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_v16_desktop.ps1
```

## Редактирование областей (новое в v16)

1. Вкладка **4. Разметка**
2. В списке **«Области»** выберите номер
3. **«Редактировать точки выбранной области»**
4. Тяните жёлтые точки мышью
5. Клик **по линии** — новая точка
6. **Delete** или **Backspace** — убрать выбранную точку (сначала кликните по ней; минимум 3). Или кнопка **«Удалить выбранную точку»**
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
